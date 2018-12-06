from sequencer import Sequencer
from display import Display
from time import sleep, time
from datetime import datetime
import curses
from constants import *
import mido
from json import dump, load
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--set", help="Filename of previous set to load", type=str)
args = parser.parse_args()
print(args.set)

class Controller(object):
    """docstring for Controller."""
    def __init__(self, display, mport, mportin):
        super(Controller, self).__init__()
        self.mport = mport
        self.mportin = mportin
        self.mportin.callback = self.process_incoming_midi()
        # Check for loading previous set
        if args.set:
            saved = args.set
            with open(saved, 'r') as saved_file:
                saved_set = load(saved_file)
            self.sequencer = Sequencer(mport, saved=saved_set)
        else:
            self.sequencer = Sequencer(mport, saved=None)
        self.last = time()
        self.display = display
        self.beatclockcount = 0
        self.save_on_exit = False

    def run(self):
        self.draw()
        while True:
            self.get_keys()
            sleep(0.05)
        pass

    def process_incoming_midi(self):
        def _process_incoming_midi(message, timestamp=0):
            '''Check for incoming midi messages and categorize so we can do something with them'''
            tick = False
            notes = []
            if message.type == "clock":
                tick = self.process_midi_tick()
                if tick:
                    self.sequencer.step_beat()
                    self.draw()
            if message.type == "note_on":
                self.sequencer.add_notes_from_midi([message.note])
        return _process_incoming_midi

    def get_keys(self):
        # TODO Refactor this to generalize command structure
        # No differentiation between key and mouse events
        c, m = self.display.getch()
        if c == -1:
            return None
        if c == ord('Q'):
            if self.save_on_exit:
                self.save()
            exit()
        if c == ord('s'):
            self.save_on_exit = not self.save_on_exit
            logging.info(self.save_on_exit)
        if c == ord('S'):
            self.save()
        if c == ord(' '):
            self.sequencer.step_beat()
        if c == ord('`'):
            self.sequencer.clear_page()
        if c == ord('n'):
            self.sequencer.cycle_key(-1)
        if c == ord('m'):
            self.sequencer.cycle_key(1)
        if c == ord('['):
            self.sequencer.change_division(-1)
        if c == ord(']'):
            self.sequencer.change_division(1)
        if c == ord('v'):
            self.sequencer.cycle_scale(-1)
        if c == ord('b'):
            self.sequencer.cycle_scale(1)
        if c == ord('c'):
            self.sequencer.swap_drum_inst()
        if c == ord('z'):
            self.sequencer.change_octave(-1)
        if c == ord('x'):
            self.sequencer.change_octave(1)
        if m != None:
            # x = self.display.get_mouse_zone(m)
            if m['zone'] == 'note':
                self.sequencer.touch_note(m['x'], m['y'])
            elif m['zone'] == 'ins':
                self.sequencer.current_visible_instrument = m['ins']
            elif m['zone'] == 'inc_rep':
                self.sequencer.inc_rep(m['page'])
            elif m['zone'] == 'dec_rep':
                self.sequencer.dec_rep(m['page'])
            elif m['zone'] == 'add_page':
                self.sequencer.add_page()
            elif m['zone'] == 'change_division':
                self.sequencer.change_division(m['div'])
        return str(c)

    def process_midi_tick(self):
        '''Perform midi tick subdivision so ticks only happen on beats'''
        self.beatclockcount += 1
        if self.beatclockcount >= 3:
            self.beatclockcount %= 3
            return True
        return False

    def draw(self):
        status = self.sequencer.get_status()
        led_grid = self.sequencer.get_led_grid()
        self.display.draw_all(status, led_grid)

    def save(self):
        print("Saving current grid to {}.cell".format(datetime.now()))
        filename = './saved/' + str(datetime.now()).split('.')[0] + '.json'
        with open(filename, 'w') as savefile:
            saved = self.sequencer.save()
            dump(saved, savefile)


def main(stdscr):
    m = curses.mousemask(1)
    curses.mouseinterval(10)
    stdscr.nodelay(1)
    display = Display(stdscr)
    with mido.open_output('SuperCell_Out', autoreset=True, virtual=True) as mport:
        with mido.open_input('SuperCell_In', autoreset=True, virtual=True) as mportin:
            controller = Controller(display, mport, mportin)
            controller.run()

    controller.run()

if __name__ == '__main__':
    curses.wrapper(main)
