if __name__ == '__main__':
    KMC = KineticMountController(number_of_devices=3)
    
    shutter, a_hwp, b_hwp = KMC.devices

    def set_alice_angle(angle):
        a_hwp.set_angle(angle)
    
    def set_bob_angle(angle):
        b_hwp.set_angle(angle)

    thread1 = threading.Thread(target=set_alice_angle, args=(90))
    thread2 = threading.Thread(target=set_bob_angle, args=())

    a_hwp.home()
    b_hwp.home()
    time.sleep(1)
    for _ in range(10):
        time.sleep(0)
        time.sleep(0)

    #shutter.home()
    #shutter.open()

