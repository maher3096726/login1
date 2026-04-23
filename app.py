from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import time
import requests
import os
import re
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import certifi
from flask_cors import CORS



app = Flask(__name__)
app.secret_key = 'd22b57f7d2c6a83c08766f886cb9c827'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)
# ===================== Firebase =====================
FIREBASE_URL = "https://hims-89bfb-default-rtdb.firebaseio.com/students.json"

def save_to_firebase(student_data, image_path_card=None, image_path_id=None):
    """حفظ البيانات في Firebase"""
    try:
        data_to_send = {
            'student_name': student_data.get('name', ''),
            'student_phone': student_data.get('phone', ''),
            'seat_number': student_data.get('seat', ''),
            'national_id': student_data.get('national_id', ''),
            'receipt_number': student_data.get('receipt_number', ''),
            'card_image_path': image_path_card if image_path_card else '',
            'id_image_path': image_path_id if image_path_id else '',
            'confidence': student_data.get('confidence', 0),
            'timestamp': int(time.time() * 1000),
            'platform': 'Web',
            'auto_extracted': True
        }
        
        response = requests.post(
            FIREBASE_URL,
            json=data_to_send,
            timeout=15,
            verify=certifi.where()
        )
        
        if response.status_code == 200:
            print("✅ تم حفظ البيانات في Firebase")
            return True
        else:
            print(f"❌ فشل الحفظ: {response.status_code}")
            return save_locally(data_to_send)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return save_locally(data_to_send)

def save_locally(data):
    """حفظ محلي"""
    try:
        filename = f"student_data_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# ===================== EasyOCR =====================
ocr_reader = None

def init_ocr():
    global ocr_reader
    try:
        import easyocr
        ocr_reader = easyocr.Reader(['ar', 'en'], gpu=False, verbose=False)
        print("✅ تم تهيئة OCR بنجاح")
        return True
    except Exception as e:
        print(f"❌ فشل تهيئة OCR: {e}")
        return False

# ===================== دوال مساعدة =====================
def preprocess_image_for_ocr(img_path):
    """معالجة الصورة لتحسين دقة OCR للأرقام"""
    try:
        img = Image.open(img_path)
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        img = img.filter(ImageFilter.SHARPEN)
        processed_path = img_path.replace('.jpg', '_processed.jpg')
        img.save(processed_path)
        return processed_path
    except Exception as e:
        print(f"خطأ في معالجة الصورة: {e}")
        return img_path

def cleanup_temp_files(*paths):
    """حذف الملفات المؤقتة"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except:
            pass

def save_temp_image(image_data):
    """حفظ الصورة المؤقتة"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        
        filename = f"temp_{int(time.time())}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img.save(filepath, quality=95)
        return filepath
    except Exception as e:
        print(f"خطأ في حفظ الصورة: {e}")
        return None

# ===================== استخراج البيانات من ورقة الاختيار =====================
def extract_data_from_card(image_data):
    """استخراج البيانات من ورقة الاختيار"""
    global ocr_reader
    if ocr_reader is None:
        if not init_ocr():
            return None
    
    try:
        img_path = save_temp_image(image_data)
        if not img_path:
            return None
        
        processed_path = preprocess_image_for_ocr(img_path)
        result = ocr_reader.readtext(processed_path, paragraph=False)
        
        words_with_pos = []
        for (bbox, text, conf) in result:
            x_center = (bbox[0][0] + bbox[2][0]) / 2
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            words_with_pos.append({
                'text': text,
                'x': x_center,
                'y': y_center,
                'bbox': bbox
            })
        
        words_with_pos.sort(key=lambda w: (w['y'], w['x']))
        full_text = " ".join([item['text'] for item in words_with_pos])
        print(f"النص المستخرج من ورقة الاختيار: {full_text[:300]}...")
        
        extracted = {
            'name': '', 'name_details': '', 'seat': '', 'seat_details': '',
            'receipt_number': '', 'receipt_details': '', 'national_id': '',
            'national_id_details': '', 'phone': '', 'phone_details': '', 'confidence': 0
        }
        
        # استخراج الاسم
        name_patterns = [
            r'(?:اسم الطالب|الاسم|Name|Student Name)[:\s]+([أ-يءآإؤةئ\s]{5,50})',
            r'الطالب[:\s]+([أ-يءآإؤةئ\s]{5,50})'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'[0-9@#$%^&*()]', '', name)
                if len(name) > 5:
                    extracted['name'] = name
                    extracted['name_details'] = f"✓ تم الاستخراج من التسمية: {name[:40]}"
                    extracted['confidence'] += 35
                    break
        
        if not extracted['name']:
            arabic_names = re.findall(r'([أ-يءآإؤةئ]{3,}(?:\s+[أ-يءآإؤةئ]{3,}){2,4})', full_text)
            if arabic_names:
                extracted['name'] = arabic_names[0][:50]
                extracted['name_details'] = f"⚠ تم الاستخراج كأسماء عربية: {extracted['name'][:40]}"
            else:
                extracted['name_details'] = "✗ لم يتم العثور على اسم"
        
        # استخراج رقم الجلوس
        seat_patterns = [
            r'(?:رقم الجلوس|جلوس|Seat No|Seat Number)[:\s]+(\d{5,7})',
            r'(?:الجلوس)[:\s]+(\d{5,7})'
        ]
        for pattern in seat_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted['seat'] = match.group(1)
                extracted['seat_details'] = f"✓ تم الاستخراج من التسمية: {match.group(1)}"
                extracted['confidence'] += 30
                break
        
        if not extracted['seat']:
            numbers = re.findall(r'\b(\d{5,7})\b', full_text)
            for num in numbers:
                if not num.startswith('01') and 5 <= len(num) <= 7:
                    extracted['seat'] = num
                    extracted['seat_details'] = f"⚠ تم الاستخراج كرقم: {num} (غير مؤكد)"
                    break
            if not extracted['seat']:
                extracted['seat_details'] = "✗ لم يتم العثور على رقم جلوس"
        
        # استخراج رقم الإيصال
        receipt_patterns = [
            r'(?:رقم الإيصال|إيصال|Receipt No|Receipt Number)[:\s]+(\d{7,12})',
            r'(?:الإيصال)[:\s]+(\d{7,12})'
        ]
        for pattern in receipt_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted['receipt_number'] = match.group(1)
                extracted['receipt_details'] = f"✓ تم الاستخراج من التسمية: {match.group(1)}"
                extracted['confidence'] += 25
                break
        
        if not extracted['receipt_number']:
            long_numbers = re.findall(r'\b(\d{8,12})\b', full_text)
            if long_numbers:
                extracted['receipt_number'] = long_numbers[0]
                extracted['receipt_details'] = f"⚠ تم الاستخراج كرقم طويل: {long_numbers[0]}"
            else:
                extracted['receipt_details'] = "✗ لم يتم العثور على رقم إيصال"
        
        # استخراج الرقم القومي من الورقة
        national_patterns = [
            r'(?:الرقم القومي|National ID|رقم قومي)[:\s]+(\d{14})',
            r'\b(\d{14})\b'
        ]
        for pattern in national_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                extracted['national_id'] = matches[0]
                extracted['national_id_details'] = f"✓ تم الاستخراج من الورقة: {matches[0]}"
                extracted['confidence'] += 25
                break
        if not extracted['national_id']:
            extracted['national_id_details'] = "✗ لم يتم العثور على رقم قومي (سيتم من البطاقة)"
        
        # استخراج رقم الهاتف
        phone_patterns = [
            r'(?:رقم الهاتف|الهاتف|تليفون|موبايل|Phone|Mobile)[:\s]+(01[0-9]{9})',
            r'(?:رقم)[:\s]+(01[0-9]{9})',
            r'\b(01[0-9]{9})\b'
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                extracted['phone'] = matches[0]
                extracted['phone_details'] = f"✓ تم الاستخراج من التسمية: {matches[0]}"
                extracted['confidence'] += 20
                break
        if not extracted['phone']:
            extracted['phone_details'] = "✗ لم يتم العثور على رقم هاتف"
        
        cleanup_temp_files(img_path, processed_path)
        return extracted
    except Exception as e:
        print(f"خطأ في الاستخراج: {e}")
        return None

# ===================== استخراج الرقم القومي من البطاقة (الحل المحدث) =====================
def extract_national_id_from_id_card(image_data):
    """
    استخراج الرقم القومي فقط من البطاقة الشخصية (14 رقم)
    تم التعديل: دعم الأرقام العربية (.المكتوبه زي كده ٢٠٦١.٠٠.٠٠.٠٠.٠٠.٠٠.٠٠.٠٠.٩٨)
    وتحويلها إلى أرقام إنجليزية وإزالة النقاط
    """
    global ocr_reader
    if ocr_reader is None:
        if not init_ocr():
            return None, "فشل تهيئة OCR"
    
    try:
        img_path = save_temp_image(image_data)
        if not img_path:
            return None, "فشل حفظ الصورة"
        
        # معالجة الصورة
        img = Image.open(img_path)
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        img = img.filter(ImageFilter.SHARPEN)
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        processed_path = img_path.replace('.jpg', '_processed.jpg')
        img.save(processed_path)
        
        # استخراج النص (باستخدام اللغة العربية والإنجليزية معاً)
        result = ocr_reader.readtext(processed_path, paragraph=False, detail=0)
        full_text = " ".join(result)
        print(f"النص الخام من البطاقة: {full_text}")
        
        # ========== الخطوة 1: تحويل الأرقام العربية إلى إنجليزية ==========
        arabic_to_english = {
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }
        
        def convert_arabic_numbers(text):
            """تحويل أي أرقام عربية في النص إلى أرقام إنجليزية"""
            for arabic, english in arabic_to_english.items():
                text = text.replace(arabic, english)
            return text
        
        # تحويل النص بالكامل
        full_text_converted = convert_arabic_numbers(full_text)
        print(f"النص بعد تحويل الأرقام: {full_text_converted}")
        
        # ========== الخطوة 2: إزالة جميع الفواصل (نقاط، شرطات، مسافات) ==========
        # إزالة كل ما ليس رقم (مع الحفاظ على الأرقام فقط)
        # لكننا نريد التعامل مع النقاط كفواصل، لذا نزيلها أولاً
        text_no_separators = re.sub(r'[\.\-–\s]', '', full_text_converted)
        print(f"النص بعد إزالة الفواصل: {text_no_separators}")
        
        # ========== الخطوة 3: البحث عن 14 رقماً متتالياً ==========
        # الطريقة المباشرة: البحث عن 14 رقم في النص المنظف
        match = re.search(r'(\d{14})', text_no_separators)
        if match:
            national_id = match.group(1)
            # تحقق إضافي: الرقم القومي المصري عادة يبدأ بـ 2 أو 3
            if national_id[0] in ['2', '3']:
                print(f"✅ تم استخراج الرقم القومي بنجاح: {national_id}")
                cleanup_temp_files(img_path, processed_path)
                return national_id, f"✓ تم استخراج الرقم القومي: {national_id}"
            else:
                # قد يكون الرقم صحيحاً لكن يبدأ برقم آخر (نادر)
                print(f"⚠ تم استخراج 14 رقم ولكن بداية غير معتادة: {national_id}")
                cleanup_temp_files(img_path, processed_path)
                return national_id, f"✓ تم استخراج الرقم القومي (بداية غير معتادة): {national_id}"
        
        # ========== الخطوة 4: البحث عن أرقام متفرقة ثم دمجها ==========
        # استخراج كل الكتل الرقمية (قد تكون متفرقة بسبب النقاط)
        numeric_blocks = re.findall(r'\d+', full_text_converted)
        all_digits = ''.join(numeric_blocks)
        print(f"جميع الأرقام المدمجة: {all_digits}")
        
        if len(all_digits) >= 14:
            # البحث عن 14 رقم متتالي في النص المدمج
            for i in range(len(all_digits) - 13):
                candidate = all_digits[i:i+14]
                if candidate[0] in ['2', '3']:
                    print(f"✅ تم استخراج الرقم القومي من الأرقام المدمجة: {candidate}")
                    cleanup_temp_files(img_path, processed_path)
                    return candidate, f"✓ تم استخراج الرقم القومي: {candidate}"
            
            # إذا لم نجد بداية مناسبة، نأخذ أول 14 رقم
            first_14 = all_digits[:14]
            print(f"⚠ تم استخراج أول 14 رقم كحل احتياطي: {first_14}")
            cleanup_temp_files(img_path, processed_path)
            return first_14, f"✓ تم استخراج الرقم القومي (احتياطي): {first_14}"
        
        # ========== الخطوة 5: فشل الاستخراج ==========
        cleanup_temp_files(img_path, processed_path)
        
        if len(all_digits) > 0:
            return None, f"✗ لم يتم العثور على 14 رقماً متتالياً. الأرقام الموجودة: {all_digits[:50]}..."
        else:
            return None, "✗ لم يتم العثور على أي أرقام في البطاقة. يرجى التأكد من وضوح الصورة والإضاءة."
        
    except Exception as e:
        print(f"خطأ في استخراج الرقم القومي: {e}")
        return None, f"خطأ في المعالجة: {str(e)}"

def validate_card_data(extracted):
    """التحقق من صحة البيانات المستخرجة"""
    if not extracted:
        return False, "لم يتم استخراج أي بيانات"
    if not extracted.get('seat'):
        return False, "لم يتم العثور على رقم الجلوس"
    return True, "صالح"

# ===================== Routes =====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/sersh')
def sersh():
    return render_template('sersh.html')

@app.route('/location')
def location():
    return render_template('location.html')

@app.route('/next')
def next_page():
    return render_template('next.html')

@app.route('/faq_detail')
def faq_detail():
    question = request.args.get('q', '')
    answer = request.args.get('a', '')
    return render_template('faq_detail.html', question=question, answer=answer)

@app.route('/api/extract_card', methods=['POST'])
def extract_card():
    """API لاستخراج بيانات ورقة الاختيار"""
    data = request.json
    image_data = data.get('image', '')
    
    if not image_data:
        return jsonify({'success': False, 'message': 'لم يتم استلام الصورة'})
    
    extracted = extract_data_from_card(image_data)
    is_valid, message = validate_card_data(extracted)
    
    if not is_valid:
        return jsonify({'success': False, 'message': message, 'data': extracted})
    
    return jsonify({
        'success': True,
        'data': extracted,
        'message': 'تم استخراج البيانات بنجاح'
    })

@app.route('/api/extract_national_id', methods=['POST'])
def extract_national_id():
    """API لاستخراج الرقم القومي فقط من البطاقة الشخصية"""
    data = request.json
    image_data = data.get('image', '')
    
    if not image_data:
        return jsonify({'success': False, 'message': 'لم يتم استلام الصورة'})
    
    national_id, details = extract_national_id_from_id_card(image_data)
    
    if not national_id:
        return jsonify({'success': False, 'message': details})
    
    return jsonify({
        'success': True,
        'national_id': national_id,
        'details': details
    })

@app.route('/api/save_student', methods=['POST'])
def save_student():
    """API لحفظ بيانات الطالب كاملة"""
    data = request.json
    student_data = data.get('student_data', {})
    card_image = data.get('card_image', '')
    id_image = data.get('id_image', '')
    
    card_path = None
    id_path = None
    
    if card_image:
        card_path = save_temp_image(card_image)
    if id_image:
        id_path = save_temp_image(id_image)
    
    success = save_to_firebase(student_data, card_path, id_path)
    
    return jsonify({
        'success': success,
        'message': 'تم حفظ البيانات بنجاح' if success else 'حدث خطأ في الحفظ'
    })

# الأسئلة الشائعة (FAQ)
FAQ_DATA = [
    {
        'id': 1,
        'question': 'عن المعهد العالي للعلوم الإدارية ببلقاس',
        'answer': """🏫 المعهد العالي للعلوم الإدارية ببلقاس
📅 التأسيس: تأسس عام 1996 بقرار وزاري رقم 1030
🎯 الرؤية: الريادة في تقديم تعليم إداري وتجاري متميز
📜 الرسالة: تقديم برامج تعليمية وبحثية وتدريبية متميزة"""
    },
    {
        'id': 2,
        'question': 'البرامج الأكاديمية بالمعهد',
        'answer': """🎓 برامج البكالوريوس (4 سنوات):
• قسم إدارة الأعمال
• قسم المحاسبة
• قسم نظم المعلومات الإدارية
• قسم التسويق

📋 برامج الدبلوم:
• الدبلوم المهني في إدارة الأعمال
• الدبلوم المهني في المحاسبة"""
    },
    {
        'id': 3,
        'question': 'شروط القبول والتسجيل للعام الدراسي',
        'answer': """📝 شروط القبول:
• الحصول على شهادة الثانوية العامة
• ألا يقل عمر المتقدم عن 17 عاماً
• اللياقة الطبية
• حسن السير والسلوك"""
    },
    {
        'id': 4,
        'question': 'الرسوم والمصروفات الدراسية',
        'answer': """💰 المصروفات الدراسية:
• الفصل الدراسي الواحد: 6,000 جنيه
• رسوم التسجيل: 1,500 جنيه
• خصومات للتفوق الأكاديمي تصل إلى 20%"""
    }
]

@app.route('/api/faq')
def get_faq():
    return jsonify(FAQ_DATA)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
