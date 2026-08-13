import time
import threading

try:
    import RPi.GPIO as GPIO
    import smbus

    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("RPi.GPIO or smbus not found. Hardware features disabled.")

# --- BUZZER ---
BUZZER_PIN = 4
pwm = None
bus = None
_initialized = False


def init_hardware():
    global pwm, bus, _initialized
    if _initialized:
        return
    _initialized = True

    if not HARDWARE_AVAILABLE:
        return

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        pwm = GPIO.PWM(BUZZER_PIN, 1000)
    except Exception as e:
        print(f"Error initializing buzzer: {e}")
        pwm = None

    try:
        bus = smbus.SMBus(1)
        lcd_init()
    except Exception as e:
        print(f"Error initializing LCD: {e}")
        bus = None


def play_tone(freq, duration):
    if pwm is None:
        return
    try:
        if freq == 0:
            pwm.stop()
        else:
            pwm.ChangeFrequency(freq)
            pwm.start(5)
        time.sleep(duration)
        pwm.stop()
    except:
        pass


def success_sound():
    def _play():
        play_tone(1200, 0.05)
        play_tone(1500, 0.05)
        play_tone(2000, 0.1)

    threading.Thread(target=_play, daemon=True).start()


def error_sound():
    def _play():
        play_tone(300, 0.15)
        play_tone(200, 0.15)

    threading.Thread(target=_play, daemon=True).start()


def special_sound():
    def _play():
        for _ in range(5):
            play_tone(2500, 0.05)
            time.sleep(0.05)

    threading.Thread(target=_play, daemon=True).start()


# --- LCD I2C ---
I2C_ADDR = 0x27
LCD_WIDTH = 16
LCD_CHR = 1
LCD_CMD = 0
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
LCD_BACKLIGHT = 0x08
ENABLE = 0b00000100


def lcd_init():
    if not bus:
        return
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    time.sleep(0.005)


def lcd_byte(bits, mode):
    if not bus:
        return
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    try:
        bus.write_byte(I2C_ADDR, bits_high)
        lcd_toggle_enable(bits_high)
        bus.write_byte(I2C_ADDR, bits_low)
        lcd_toggle_enable(bits_low)
    except:
        pass


def lcd_toggle_enable(bits):
    if not bus:
        return
    try:
        time.sleep(0.0005)
        bus.write_byte(I2C_ADDR, (bits | ENABLE))
        time.sleep(0.0005)
        bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
        time.sleep(0.0005)
    except:
        pass


def lcd_string(message, line):
    if not bus:
        return
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


last_hp1 = -1
last_hp2 = -1


def update_lcd(hp1, hp2):
    global last_hp1, last_hp2
    if not bus:
        return
    if hp1 == last_hp1 and hp2 == last_hp2:
        return
    last_hp1 = hp1
    last_hp2 = hp2
    lcd_string(f"P1 HP: {hp1}/100", LCD_LINE_1)
    lcd_string(f"P2 HP: {hp2}/100", LCD_LINE_2)
