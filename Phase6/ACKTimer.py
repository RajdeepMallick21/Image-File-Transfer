import threading
import time

timer_event = threading.Event()
def timer():
    time_value = 0.03
    while time_value:
        if timer_event.is_set():
            #print("STOPPING TIMER")
            break
        else:
            time.sleep(0.01)
            time_value -= 0.01
            #print(time_value)

if __name__ == '__main__':
    test_thread = threading.Thread(target=timer)
    test_thread.start()
    time.sleep(5)
    #timer_event.set()

