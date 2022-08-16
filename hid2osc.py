#f.olofsson 2019

# required Python libraries: pyliblo, hid, pyusb
# example: sudo python HIDtoOSC.py --vid 6700 --pid 2 --port 12002 --debug
# note: macOS must be running this as root if the device is a keyboard

import sys, argparse
import usb.core, hid

from pythonosc import udp_client

def event_generator(handler):
    prev_set = set([0])
    while True:
        usb_input = yield
        current_set = set(usb_input[2:])

        pressed_set = current_set.difference(prev_set)
        while len(pressed_set):
            code = pressed_set.pop()
            handler(usb_input[0], code, True)

        released_set = prev_set.difference(current_set)
        while len(released_set):
            code = released_set.pop()
            handler(usb_input[0], code, False)

        prev_set = current_set

#--settings

#--arguments
parser= argparse.ArgumentParser()
parser.add_argument('--vid', type= int, dest= 'vid', help= 'set HID vendor id')
parser.add_argument('--pid', type= int, dest= 'pid', help= 'set HID product id')
parser.add_argument('--ip', dest= 'ip', help= 'set OSC destination IP')
parser.add_argument('--port', type= int, dest= 'port', help= 'set OSC destination port')
parser.add_argument('--rate', type= int, dest= 'rate', help= 'update rate in milliseconds')
parser.add_argument('--debug', dest= 'debug', action= 'store_true', help= 'post incoming HID data')

parser.set_defaults(vid= 0)
parser.set_defaults(pid= 0)
parser.set_defaults(ip= '127.0.0.1')
parser.set_defaults(port= 9001)
parser.set_defaults(rate= 100)
parser.set_defaults(debug= False)
args= parser.parse_args()

if args.debug:
    print('Available HID devices:')
    for d in hid.enumerate():
        print('  device: %s, %s'%(d['manufacturer_string'], d['product_string']))
        print('  vid: %s, pid: %s'%(d['vendor_id'], d['product_id']))

def main():
    dev= usb.core.find(idVendor= args.vid, idProduct= args.pid)

    if dev is None:
        sys.exit('Could not find device %s, %s'%(args.vid, args.pid))


    for config in dev:
        for i in range(config.bNumInterfaces):
            if dev.is_kernel_driver_active(i):
                # print(f"detach config: {config} interface: {i}")
                dev.detach_kernel_driver(i)

    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        sys.exit('Could not set configuration: %s'%str(e))

    endpoint= dev[0][(0, 0)][0]

    if args.debug:
        print(endpoint)

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    def handle_key(modifier, key, state):
        if args.debug:
            print(f"{key} is {'pressed' if state else 'released'}, modifier: {modifier}")
        client.send_message("/keyboard", [key, int(state), modifier])

    noerror= True
    data=None

    eg = event_generator(handle_key)
    next(eg)

    while noerror:
        try:
            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, args.rate)
        except Exception as e:
            if str(e).find("110") == -1:
                noerror= False
                print(f"read err: {e}")
                try:
                    dev.close()
                    print(f'Closed the hid device')
                except:
                    pass

        if data:
            if args.debug:
                pass
                # print([x for x in data])
            eg.send(data)

if __name__=='__main__':
  main()
