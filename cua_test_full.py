import json, os, time, base64
from pathlib import Path
from crm.android_cua import CuaManager, _sh_available
from crm.google_auth import get_service
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

print("=== Iniciando prueba completa de CUA ===")
print("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()))

# Initialize CuaManager
cua = CuaManager()
print(f"Resolución del dispositivo: {cua.resolution[0]}x{cua.resolution[1]}")

# Check Shizuku availability
print("\n--- Verificando disponibilidad de Shizuku ---")
if _sh_available():
    print("✅ Shizuku está disponible y responde.")
else:
    print("❌ Shizuku NO está disponible o no responde.")
    print("   Esto impedirá que CUA funcione correctamente.")
    # We'll continue anyway to see what happens

# Prepare to collect results
test_results = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "device_resolution": f"{cua.resolution[0]}x{cua.resolution[1]}",
    "shizuku_available": _sh_available(),
    "steps": [],
    "screenshots": [],
    "errors": []
}

def log_step(description, success=True, details=None):
    step = {
        "time": time.strftime("%H:%M:%S"),
        "description": description,
        "success": success,
        "details": details or {}
    }
    test_results["steps"].append(step)
    status = "✅" if success else "❌"
    print(f"{status} {description}")
    if details:
        for k, v in details.items():
            print(f"   {k}: {v}")

# Function to take screenshot and save it
def take_screenshot(label):
    try:
        timestamp = int(time.time())
        filename = f"cua_test_{label}_{timestamp}.png"
        path = cua.screenshot(filename)
        if path:
            # Read the screenshot data
            with open(path, 'rb') as f:
                img_data = f.read()
            test_results["screenshots"].append({
                "label": label,
                "filename": filename,
                "path": path,
                "size": len(img_data)
            })
            log_step(f"Captura de pantalla tomada: {label}", True, {"filename": filename, "size_bytes": len(img_data)})
            return img_data
        else:
            log_step(f"Fallo al tomar captura de pantalla: {label}", False)
            return None
    except Exception as e:
        log_step(f"Error al tomar captura de pantalla: {label}", False, {"error": str(e)})
        return None

# Function to send email via Gmail
def send_email_report(recipient, subject, body, attachments=None):
    try:
        # Get Gmail service
        gmail_service = get_service('gmail', 'v1', 'gmail')
        if not gmail_service:
            log_step("No se pudo obtener servicio de Gmail", False)
            return False
        
        # Create message
        message = MIMEMultipart()
        message['to'] = recipient
        message['subject'] = subject
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Add attachments if any
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {att["filename"]}',
                )
                message.attach(part)
        
        # Encode and send
        raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw_string}
        
        sent_message = gmail_service.users().messages().send(userId='me', body=message_body).execute()
        log_step(f"Correo enviado a {recipient}", True, {"message_id": sent_message['id']})
        return True
    except Exception as e:
        log_step(f"Error al enviar correo: {e}", False)
        return False

# Start test
print("\n--- Iniciando secuencia de prueba CUA ---")

# Step 1: Initial state and screenshot
log_step("Obteniendo estado inicial de la UI")
try:
    initial_ui = cua.ui_text_summary(max_elements=15)
    test_results["steps"][-1]["details"]["initial_ui_summary"] = initial_ui[:500] + ("..." if len(initial_ui) > 500 else "")
except Exception as e:
    log_step("Error al obtener UI inicial", False, {"error": str(e)})

initial_shot = take_screenshot("initial")

# Step 2: Open Settings app
log_step("Intentando abrir aplicación de Configuración")
try:
    success = cua.open_app('com.android.settings')
    log_step("Comando para abrir Configuración enviado", success, {"result": success})
    test_results["steps"][-1]["details"]["open_app_result"] = success
    if success:
        time.sleep(3)  # Wait for app to open
    else:
        test_results["errors"].append("Failed to open Settings app")
except Exception as e:
    log_step("Excepción al intentar abrir Configuración", False, {"error": str(e)})
    test_results["errors"].append(f"Exception opening Settings: {e}")

# Step 3: After opening Settings
log_step("Obteniendo estado después de abrir Configuración")
try:
    ui_after_open = cua.ui_text_summary(max_elements=15)
    test_results["steps"][-1]["details"]["ui_after_open_summary"] = ui_after_open[:500] + ("..." if len(ui_after_open) > 500 else "")
except Exception as e:
    log_step("Error al obtener UI después de abrir app", False, {"error": str(e)})

shot_after_open = take_screenshot("after_open_settings")

# Step 4: Try to tap on a common element (e.g., Wi-Fi)
log_step("Intentando encontrar y tocar elemento 'Wi-Fi'")
try:
    # First, dump UI to see what's available
    elements = cua.dump_ui()
    wifi_elements = [e for e in elements if e.text and 'wifi' in e.text.lower() or e.content_desc and 'wifi' in e.content_desc.lower()]
    if wifi_elements:
        # Try to tap the first Wi-Fi element
        tap_success = cua.tap_element(wifi_elements[0])
        log_step("Intento de tocar elemento Wi-Fi", tap_success, {"element_text": wifi_elements[0].text, "bounds": wifi_elements[0].bounds})
        if tap_success:
            time.sleep(2)  # Wait for action to complete
            ui_after_tap = cua.ui_text_summary(max_elements=10)
            test_results["steps"][-1]["details"]["ui_after_wifi_tap"] = ui_after_tap[:300] + ("..." if len(ui_after_tap) > 300 else "")
            take_screenshot("after_wifi_tap")
        else:
            test_results["errors"].append("Failed to tap Wi-Fi element")
    else:
        log_step("No se encontró elemento Wi-Fi en la UI actual", False)
        # Try to scroll down to see more
        scroll_success = cua.scroll_down()
        log_step("Intento de desplazamiento hacia abajo", scroll_success)
        if scroll_success:
            time.sleep(1)
            ui_after_scroll = cua.ui_text_summary(max_elements=10)
            test_results["steps"][-1]["details"]["ui_after_scroll"] = ui_after_scroll[:300] + ("..." if len(ui_after_scroll) > 300 else "")
            take_screenshot("after_scroll_down")
except Exception as e:
    log_step("Error durante intento de tocar Wi-Fi", False, {"error": str(e)})
    test_results["errors"].append(f"Exception in Wi-Fi tap attempt: {e}")

# Step 5: Try inputting text (if we can find a field)
log_step("Intentando ingresar texto en un campo editable")
try:
    # Look for edittext or input fields
    elements = cua.dump_ui()
    input_elements = [e for e in elements if 'edittext' in e.class_name.lower()]
    if input_elements:
        # Tap the first input field
        cua.tap_element(input_elements[0])
        time.sleep(1)
        # Input some text
        input_success = cua.input_text("Prueba CUA desde OpenClaw")
        log_step("Intento de ingresar texto", input_success)
        if input_success:
            time.sleep(1)
            take_screenshot("after_input_text")
        # Press enter to submit
        cua.press_key("enter")
        time.sleep(1)
    else:
        log_step("No se encontraron campos de entrada de texto", False)
except Exception as e:
    log_step("Error durante intento de ingreso de texto", False, {"error": str(e)})

# Step 6: Go back home
log_step("Intentando regresar a la pantalla de inicio")
try:
    home_success = cua.go_home()
    log_step("Comando para ir a Home enviado", home_success, {"result": home_success})
    if home_success:
        time.sleep(2)
        final_ui = cua.ui_text_summary(max_elements=10)
        test_results["steps"][-1]["details"]["final_ui_summary"] = final_ui[:300] + ("..." if len(final_ui) > 300 else "")
        final_shot = take_screenshot("final_home")
    else:
        test_results["errors"].append("Failed to go home")
except Exception as e:
    log_step("Excepción al intentar ir a Home", False, {"error": str(e)})
    test_results["errors"].append(f"Exception going home: {e}")

# Step 7: Final screenshot
final_shot = take_screenshot("end")

# Compile report
report_lines = [
    "=== INFORME DE PRUEBA CUA ===",
    f"Timestamp: {test_results['timestamp']}",
    f"Resolución del dispositivo: {test_results['device_resolution']}",
    f"Shizuku disponible: {test_results['shizuku_available']}",
    "",
    "=== RESUMEN DE PASOS ==="
]

for i, step in enumerate(test_results["steps"], 1):
    report_lines.append(f"{i}. [{step['time']}] {step['description']}")
    report_lines.append(f"   Éxito: {'Sí' if step['success'] else 'No'}")
    if step["details"]:
        for k, v in step["details"].items():
            if isinstance(v, str) and len(v) > 100:
                v = v[:100] + "..."
            report_lines.append(f"   {k}: {v}")
    report_lines.append("")

if test_results["errors"]:
    report_lines.append("=== ERRORES ENCONTRADOS ===")
    for err in test_results["errors"]:
        report_lines.append(f"- {err}")
    report_lines.append("")

report_lines.append("=== CAPTURAS DE PANTALLA TOMADAS ===")
for shot in test_results["screenshots"]:
    report_lines.append(f"- {shot['label']}: {shot['filename']} ({shot['size']} bytes)")

report_lines.append("")
report_lines.append("=== FIN DEL INFORME ===")

report_text = "\n".join(report_lines)
print("\n" + "="*50)
print("INFORME GENERADO:")
print(report_text)
print("="*50)

# Send report via Gmail
print("\n--- Intentando enviar informe por correo electrónico ---")
try:
    # Prepare attachments (screenshots)
    attachments = []
    for shot in test_results["screenshots"]:
        try:
            with open(shot["path"], 'rb') as f:
                img_data = f.read()
            attachments.append({
                "filename": shot["filename"],
                "data": img_data
            })
        except Exception as e:
            print(f"No se pudo leer la captura {shot['filename']}: {e}")
    
    # Send email
    email_sent = send_email_report(
        recipient="oficinabarreal@gmail.com",  # From earlier tests, this works
        subject=f"[OpenClaw CUA Test] Informe de prueba - {test_results['timestamp']}",
        body=report_text,
        attachments=attachments if attachments else None
    )
    
    if email_sent:
        print("✅ Informe enviado por correo electrónico exitosamente.")
    else:
        print("❌ Falló el envío del informe por correo electrónico.")
        
except Exception as e:
    print(f"❌ Error crítico al intentar enviar correo: {e}")

print("\n=== Prueba de CUA completada ===")
