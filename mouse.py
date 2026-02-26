import sys
import time
import math
import threading

running = False
lock = threading.Lock()


def toggle():
    global running
    with lock:
        running = not running
    state = "STARTED" if running else "STOPPED"
    print(f"Mouse mover {state}")


if sys.platform == "linux":
    import evdev
    from evdev import ecodes, UInput

    def find_keyboard():
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for dev in devices:
            if 'keyd virtual keyboard' in dev.name.lower():
                return dev
        for dev in devices:
            caps = dev.capabilities()
            if ecodes.EV_KEY in caps and ecodes.KEY_M in caps[ecodes.EV_KEY]:
                return dev
        return None

    def move_mouse():
        caps = {
            ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
            ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE],
        }
        ui = UInput(events=caps, name="mouse-mover")
        time.sleep(1)
        radius = 100
        steps = 120
        angle = 0
        step_angle = 2 * math.pi / steps
        while True:
            with lock:
                is_running = running
            if is_running:
                dx = int(radius * (math.cos(angle + step_angle) - math.cos(angle)))
                dy = int(radius * (math.sin(angle + step_angle) - math.sin(angle)))
                ui.write(ecodes.EV_REL, ecodes.REL_X, dx)
                ui.write(ecodes.EV_REL, ecodes.REL_Y, dy)
                ui.syn()
                angle += step_angle
                time.sleep(0.03)

    def listen_hotkeys():
        kbd = find_keyboard()
        if kbd is None:
            print("No keyboard found. Run with sudo.")
            raise SystemExit(1)
        print(f"Using keyboard: {kbd.name}")
        ctrl_held = False
        for event in kbd.read_loop():
            if event.type != ecodes.EV_KEY:
                continue
            key_event = evdev.categorize(event)
            if key_event.keycode in ('KEY_LEFTCTRL', 'KEY_RIGHTCTRL'):
                ctrl_held = key_event.keystate in (key_event.key_down, key_event.key_hold)
            elif ctrl_held and key_event.keystate == key_event.key_down:
                if key_event.keycode == 'KEY_M':
                    toggle()
                elif key_event.keycode == 'KEY_Q':
                    print("Exiting.")
                    raise SystemExit(0)

else:
    import pyautogui
    import keyboard

    pyautogui.FAILSAFE = False

    def move_mouse():
        radius = 100
        steps = 120
        angle = 0
        step_angle = 2 * math.pi / steps
        while True:
            with lock:
                is_running = running
            if is_running:
                dx = int(radius * (math.cos(angle + step_angle) - math.cos(angle)))
                dy = int(radius * (math.sin(angle + step_angle) - math.sin(angle)))
                pyautogui.moveRel(dx, dy)
                angle += step_angle
                time.sleep(0.03)
            else:
                time.sleep(0.1)

    def listen_hotkeys():
        keyboard.add_hotkey("ctrl+m", toggle)
        keyboard.wait("ctrl+q")
        print("Exiting.")


def main():
    print("Mouse Mover")
    print("-----------")
    print("Ctrl+M  : Start / Stop")
    print("Ctrl+Q  : Quit")
    print()
    print("Waiting... Press Ctrl+M to start.")

    mover_thread = threading.Thread(target=move_mouse, daemon=True)
    mover_thread.start()

    listen_hotkeys()


if __name__ == "__main__":
    main()
