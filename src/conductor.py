#coding=utf-8
from time import sleep
from constants import *
from instruments import instrument_lookup
from note_conversion import *
from save_utils import get_all_set_file_numbers, filenum_from_touch, validate_filenum, load_filenum, save_filenum


class Conductor(object):
    """docstring for Conductor."""
    # def __init__(self, mport, bars=int(W/4)):
    def __init__(self, mport, saved=None, key="e", scale="pentatonic_maj", octave=2, bars=int(W/4), height=H):
        super(Conductor, self).__init__()
        self.mport = mport
        if key not in KEYS:
            print('Requested key {} not known'.format(key))
            exit()
        self.key = key
        if scale not in SCALES.keys():
            print('Requested scale {} not known'.format(scale))
            exit()
        self.states = 'play save load ins_cfg gbl_cfg display'.split()  # Valid states for the display(s)
        self.beat_position = 0
        self.height = H
        self.width = bars*4
        self.bars = bars
        self.max_beat_division = 8
        self.scale = scale
        self.octave = octave  # Starting octave
        self.instruments = [instrument_lookup(1)(ins_num=x, **self.instrument_ctx()) for x in range(8)]
        for x in range(6):
            self.instruments.append(instrument_lookup(2)(ins_num=x+8, mport=self.mport, key=key, scale=scale, octave=octave, speed=1))
        self.instruments.append(instrument_lookup(7)(ins_num=14, mport=self.mport, key=key, scale=scale, octave=octave, speed=1))
        self.instruments.append(instrument_lookup(5)(ins_num=15, mport=self.mport, key=key, scale=scale, octave=octave, speed=1))
        self.current_visible_instrument_num = 0
        if saved:
            # If we're loading immediately, ignore all this setup and overwrite with info from file
            self.load(saved)
            self.current_state = 'play'  # Current state to be shown on display(s)
        else:
            # Otherwise, show load screen to select file (or empty)
            self.current_state = 'load'  # Current state to be shown on display(s)
        return

    def instrument_ctx(self):
        return {
            'mport': self.mport,
            'key': self.key,
            'scale': self.scale,
            'octave': self.octave,
            'speed': 1
        }

    def ins_cfg_state(self):
        if self.current_state == 'ins_cfg':
            self.current_state = 'play'
        else:
            self.current_state = 'ins_cfg'
        return

    def gbl_cfg_state(self):
        if self.current_state == 'gbl_cfg':
            self.current_state = 'play'
        else:
            self.current_state = 'gbl_cfg'
        return

    def save_state(self):
        if self.current_state == 'save':
            self.current_state = 'play'
        else:
            self.current_state = 'save'
        return

    def load_state(self):
        if self.current_state == 'load':
            self.current_state = 'play'
        else:
            self.current_state = 'load'
        return

    def get_led_grid(self):
        '''Get led status types for all cells of the grid, to be drawn by the display'''
        display_func_name = self.current_state + '_screen'
        self.__getattribute__(display_func_name)
        display_func = getattr(self, display_func_name)
        return display_func()

    def play_screen(self):
        led_grid = self.get_curr_instrument().get_led_grid(self.current_state)
        return led_grid

    def gbl_cfg_screen(self):
        led_grid = []
        for x in range(16):
            led_grid.append([LED_BLANK for y in range(16)])
        led_grid[5][5] = LED_CURSOR
        return led_grid

    def ins_cfg_screen(self):
        led_grid = self.get_curr_instrument().get_led_grid('ins_cfg')
        return led_grid

    def load_screen(self):
        led_grid = []
        for x in range(16):
            led_grid.append([LED_BLANK for y in range(16)])
        files = get_all_set_file_numbers()
        for f in files:
            if f > 254:  # TODO add a slot for empty/new
                continue
            x = int(f / 16)
            y = int(f % 16)
            led_grid[y][15-x] = LED_ACTIVE
        led_grid[0][15] = LED_CURSOR
        return led_grid


    def save_screen(self):
        return self.load_screen()

    def add_instrument(self, type):
        if len(self.instruments) == 16:
            return
        ins_type = instrument_lookup(type)
        self.instruments.append(ins_type(ins_num=len(self.instruments), **self.instrument_ctx()))
        return

    def get_status(self):
        status = self.get_curr_instrument().get_status()
        return status

    def step_beat(self):
        self.beat_position += 1
        self.beat_position %= self.width * self.max_beat_division
        for ins in self.instruments:
            # ins.step_beat()#self.beat_position)
            ins.step_beat(self.beat_position)
        pass

    def save(self, filenum=None):
        data = {
            "height": 16,
            "width": 16,
            "instruments": [i.save() for i in self.instruments]
        }
        save_filenum(data, filenum)


    def load(self, saved):
        self.height = saved['height']
        self.width = saved['width']
        self.scale = saved['instruments'][0]['scale']
        self.octave = saved['instruments'][0]['octave']
        self.key = saved['instruments'][0]['key']
        for i in range(len(saved['instruments'])):
            self.add_instrument(saved['instruments'][i]['type'])
            self.instruments[i].load(saved['instruments'][i])
        self.current_state = 'play'
        return


    ###### GETTERS/SETTERS ######

    def get_curr_instrument(self):
        return self.instruments[self.current_visible_instrument_num]

    def set_curr_instrument(self, num):
        self.current_visible_instrument_num = num

    def get_curr_instrument_num(self):
        return self.current_visible_instrument_num + 1

    def get_total_instrument_num(self):
        return len(self.instruments)

    def cycle_key(self, up_down):
        '''Find current key in master list, move on to prev/next key, set in all modal instruments'''
        curr_key = KEYS.index(self.key)
        new_key = (curr_key + up_down) % len(KEYS)
        self.key = KEYS[new_key]
        for i in self.instruments:
            i.set_key(self.key)
        return

    def cycle_scale(self, up_down):
        '''Find current scale in master list, move on to prev/next key, set in all modal instruments'''
        curr_scale = list(SCALES.keys()).index(self.scale)
        new_scale = (curr_scale + up_down) % len(SCALES.keys())
        self.scale = list(SCALES.keys())[new_scale]
        for i in self.instruments:
            # if not i.isdrum:
            i.set_scale(self.scale)
        return
    #
    # def next_instrument(self):
    #     if self.current_visible_instrument_num == len(self.instruments)-1:
    #         return False
    #     self.current_visible_instrument_num += 1
    #     return
    #
    # def prev_instrument(self):
    #     if self.current_visible_instrument_num == 0:
    #         return False
    #     self.current_visible_instrument_num -= 1
    #     return

    ###### CONTROL PASSTHROUGH METHODS ######

    def touch_note(self, x, y):
        if self.current_state == 'play':
            self.get_curr_instrument().touch_note(x, y)
        elif self.current_state == 'load':
            filenum = filenum_from_touch(x, y)
            if not validate_filenum(filenum):
                return
            self.load(load_filenum(filenum))
            self.current_state == 'play'  # TODO return to play, or stay in load?
        elif self.current_state == 'save':
            filenum = filenum_from_touch(x, y)
            if validate_filenum(filenum):
                return  # don't overwrite existing files
            self.save(filenum)
            self.current_state == 'play'  # TODO return to play, or stay in save?
        return

    def change_division(self, up_down):
        '''Find current instrument, inc or dec its beat division as appropriate'''
        self.get_curr_instrument().change_division(up_down)
        return

    def change_octave(self, up_down):
        '''Find current key in master list, move on to prev/next key, set in all modal instruments'''
        self.get_curr_instrument().change_octave(up_down)
        return

    def inc_rep(self, page):
        ins = self.get_curr_instrument()
        ins.inc_page_repeats(page)
        pass

    def dec_rep(self, page):
        ins = self.get_curr_instrument()
        ins.dec_page_repeats(page)
        pass

    def add_page(self):
        ins = self.get_curr_instrument()
        ins.add_page()
        pass

    def clear_page(self):
        self.get_curr_instrument().clear_page()
        return














import unittest
class TestInstrument(unittest.TestCase):
    def test_instrument_nums(self):
        seq = Conductor(None)
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        self.assertEqual(seq.get_total_instrument_num(), 1)
        seq.next_instrument()
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        seq.prev_instrument()
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        seq.prev_instrument()
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        seq.add_instrument("e", "major")
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        self.assertEqual(seq.get_total_instrument_num(), 2)
        seq.next_instrument()
        self.assertEqual(seq.get_curr_instrument_num(), 2)
        seq.prev_instrument()
        self.assertEqual(seq.get_curr_instrument_num(), 1)

    def test_multi_instrument_notes(self):
        seq = Conductor(None)
        seq.add_instrument("e", "major")
        seq.touch_note(0,3)
        seq.touch_note(1,4)
        self.assertEqual(seq.get_curr_instrument_num(), 1)
        self.assertEqual(seq.get_curr_instrument().get_curr_notes(), [3])
        seq.next_instrument()
        seq.touch_note(0,5)
        seq.touch_note(1,6)
        self.assertEqual(seq.get_curr_instrument_num(), 2)
        self.assertEqual(seq.get_curr_instrument().get_curr_notes(), [5])
        seq.step_beat()
        self.assertEqual(seq.get_curr_instrument().get_curr_notes(), [6])
        seq.prev_instrument()
        self.assertEqual(seq.get_curr_instrument().get_curr_notes(), [4])

    def test_led_grid(self):
        seq = Conductor(None)
        seq.touch_note(2,3)
        seq.touch_note(2,4)
        seq.touch_note(2,5)
        seq.touch_note(3,3)
        seq.touch_note(4,3)
        seq.step_beat()
        seq.step_beat()
        seq.step_beat()  # step to 4th beat, #3
        grid = seq.get_led_grid()
        print(grid)
        self.assertEqual(grid[0], [0,0,0,0,0,0,0,0,             0,0,0,0,0,0,0,0])
        self.assertEqual(grid[1], [0,0,0,0,0,0,0,0,             0,0,0,0,0,0,0,0])
        self.assertEqual(grid[2], [0,0,0,LED_ACTIVE,LED_ACTIVE,LED_ACTIVE,0,0, 0,0,0,0,0,0,0,0])
        self.assertEqual(grid[3], [LED_BEAT,LED_BEAT,LED_BEAT,LED_ACTIVE,LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT, LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT,LED_BEAT])
        self.assertEqual(grid[4], [0,0,0,LED_ACTIVE,0,0,0,0,     0,0,0,0,0,0,0,0])

if __name__ == '__main__':
    unittest.main()
