from datetime import timedelta, datetime as dt
from getkey import getkey, keys
import PySimpleGUI as sg
import networkzero as nw0
try:
    from gpiozero import Button # pyright: ignore [reportMissingImports]
except:
    class Button:
        def __init__(self, pin_id, **kwargs):
            self.pin_id = pin_id
            self.kwargs = kwargs
            print('Pseudo GPIOZERO button on pin', pin_id)

TRACK_SAFE = 1
TRACK_DANGER = 0
TRACK_NORMAL = 2
SIGNAL_DANGER = 0
SIGNAL_CLEAR = 1

TRACK_WIDTH = 5
TRACK_NORMAL_COLOR = 'yellow'
TRACK_SAFE_COLOR = 'yellow'
TRACK_DANGER_COLOR = 'red'
STUB_NORMAL_COLOR = 'yellow'
STUB_SAFE_COLOR = 'yellow'
STUB_DANGER_COLOR = 'red'
SIGNAL_CLEAR_COLOR = 'green'
SIGNAL_DANGER_COLOR = 'red'
SIGNAL_GUI_BUTTON = True
SIGNAL_WAIT_FOR_SET = False
TURNOUT_NORMAL_COLOR = 'yellow'
TURNOUT_SAFE_COLOR = 'green'
TURNOUT_DANGER_COLOR = 'red'
TURNOUT_POINT_COLOR = 'blue'
TURNOUT_GUI_BUTTON = True
TURNOUT_WAIT_FOR_SET = False
BLOCK_LABEL_COLOR = 'blue'
ROUTE_GUI_BUTTON = True
LAYOUT_LABEL_COLOR = 'blue'
LAYOUT_BACKGROUND_COLOR = 'light gray'
APPLICATION_THEME = 'LightGray2'

_supervisors = {}

def set_default(item, value):
    _item = item.upper()
    if _item == 'TRACK_NORMAL_COLOR':
        global TRACK_NORMAL_COLOR
        TRACK_NORMAL_COLOR = value
    elif _item == 'TRACK_SAFE_COLOR':
        global TRACK_SAFE_COLOR
        TRACK_SAFE_COLOR = value
    elif _item == 'TRACK_DANGER_COLOR':
        global TRACK_DANGER_COLOR
        TRACK_DANGER_COLOR = value
    elif _item == 'STUB_NORMAL_COLOR':
        global STUB_NORMAL_COLOR
        STUB_NORMAL_COLOR = value
    elif _item == 'STUB_SAFE_COLOR':
        global STUB_SAFE_COLOR
        STUB_SAFE_COLOR = value
    elif _item == 'STUB_DANGER_COLOR':
        global STUB_DANGER_COLOR
        STUB_DANGER_COLOR = value
    elif _item == 'SIGNAL_CLEAR_COLOR':
        global SIGNAL_CLEAR_COLOR
        SIGNAL_CLEAR_COLOR = value
    elif _item == 'SIGNAL_DANGER_COLOR':
        global SIGNAL_DANGER_COLOR
        SIGNAL_DANGER_COLOR = value
    elif _item == 'SIGNAL_GUI_BUTTON':
        global SIGNAL_GUI_BUTTON
        SIGNAL_GUI_BUTTON = value
    elif _item == 'SIGNAL_WAIT_FOR_SET':
        global SIGNAL_WAIT_FOR_SET
        SIGNAL_WAIT_FOR_SET = value
    elif _item == 'TURNOUT_NORMAL_COLOR':
        global TURNOUT_NORMAL_COLOR
        TURNOUT_NORMAL_COLOR = value
    elif _item == 'TURNOUT_SAFE_COLOR':
        global TURNOUT_SAFE_COLOR
        TURNOUT_SAFE_COLOR = value
    elif _item == 'TURNOUT_DANGER_COLOR':
        global TURNOUT_DANGER_COLOR
        TURNOUT_DANGER_COLOR = value
    elif _item == 'TURNOUT_POINT_COLOR':
        global TURNOUT_POINT_COLOR
        TURNOUT_POINT_COLOR = value
    elif _item == 'TURNOUT_GUI_BUTTON':
        global TURNOUT_GUI_BUTTON
        TURNOUT_GUI_BUTTON = value
    elif _item == 'TURNOUT_WAIT_FOR_SET':
        global TURNOUT_WAIT_FOR_SET
        TURNOUT_WAIT_FOR_SET = value
    elif _item == 'BLOCK_LABEL_COLOR':
        global BLOCK_LABEL_COLOR
        BLOCK_LABEL_COLOR = value
    elif _item == 'ROUTE_GUI_BUTTON':
        global ROUTE_GUI_BUTTON
        ROUTE_GUI_BUTTON = value
    elif _item == 'LAYOUT_LABEL_COLOR':
        global LAYOUT_LABEL_COLOR
        LAYOUT_LABEL_COLOR = value
    elif _item == 'LAYOUT_BACKGROUND_COLOR':
        global LAYOUT_BACKGROUND_COLOR
        LAYOUT_BACKGROUND_COLOR = value
    elif _item == 'TRACK_WIDTH':
        global TRACK_WIDTH
        TRACK_WIDTH = value
    elif _item == 'APPLICATION_THEME':
        global APPLICATION_THEME
        APPLICATION_THEME = value
    else:
        raise ValueError(f'Invalid item for setting of default value: item = {item}, value = {value}')

def _get_screen_size():
    layout = [[]]
    window = sg.Window('', layout, finalize = True)
    size = window.get_screen_size()
    window.close()
    return size

class PushButton(Button):
    PUSH_DEBOUNCE = timedelta(seconds = 0.25)

    def __init__(self, button_id, pin_id, callback):
        '''
        The pin ID should be a GPIO pin number
        '''
        super().__init__(pin_id, bounce_time = None)
        self.button_id = button_id
        self.callback = callback
        self.last_push = dt.now()
        self.when_pressed = self.pushed
    
    def pushed(self):
        now = dt.now()
        if now - self.last_push >= PushButton.PUSH_DEBOUNCE:
            self.last_push = now
            if self.callback:
                self.callback()

class Route:
    def __init__(self, id, gui_button = None, push_button = None, keyboard_event = None):
        self.id = id
        if gui_button is None:
            self.gui_button = ROUTE_GUI_BUTTON
        else:
            self.gui_button = gui_button
        if isinstance(push_button, int):
            self.push_button = PushButton(button_id = id, pin_id = push_button, callback = self.run)
        elif isinstance(push_button, PushButton):
            self.push_button = push_button
        else:
            self.push_button = None
        self.keyboard_event = keyboard_event
        self.legs = []

    def add(self, leg, does):
        self.legs.append(getattr(leg, does))

    def run(self):
        for leg in self.legs:
            leg()

class Track:
    class _Iterator:
        def __init__(self, item):
            self._item = item
            self._index = 0

        def __next__(self):
            if self._index == 0:
                self._index += 1
                return self._item
            else:
                raise StopIteration

    def __init__(self, id, start_location = None, end_location = None, state = TRACK_NORMAL, normal_color = None, safe_color = None, danger_color = None):
        self.id = id
        self.start_location = start_location
        self.end_location = end_location
        self.state = state
        if normal_color is None:
            self.normal_color = TRACK_NORMAL_COLOR
        else:
            self.normal_color = normal_color
        if safe_color is None:
            self.safe_color = TRACK_SAFE_COLOR
        else:
            self.safe_color = safe_color
        if danger_color is None:
            self.danger_color = TRACK_DANGER_COLOR
        else:
            self.danger_color = danger_color
        self.graph_id = None
        self.panel = None

    def __iter__(self):
        return self._Iterator(self)
    
    def get_start_location(self):
        return self.start_location

    def get_end_location(self):
        return self.end_location

    def get_graph_id(self):
        return self.graph_id

    def set_panel(self, panel):
        self.panel = panel

    def draw(self):
        if self.start_location and self.end_location:
            if self.state == TRACK_NORMAL:
                color = self.normal_color
            elif self.state == TRACK_SAFE:
                color = self.safe_color
            elif self.state == TRACK_DANGER:
                color = self.danger_color
            else:
                color = self.danger_color
            if self.panel:
                self.graph_id = self.panel.draw_line(self.start_location, self.end_location, color = color, width = TRACK_WIDTH)

    def clicked(self, figures):
        pass

    def erase(self):
        if self.panel:
            self.panel.delete_figure(self.graph_id)

    def safe(self):
        self.state = TRACK_SAFE
        if self.panel:
            self.panel.tk_canvas.itemconfigure(self.graph_id, fill = self.safe_color)

    def danger(self):
        self.state = TRACK_DANGER
        if self.panel:
            self.panel.tk_canvas.itemconfigure(self.graph_id, fill = self.danger_color)

class Stub:
    class _Iterator:
        def __init__(self, item):
            self._item = item
            self._index = 0

        def __next__(self):
            if self._index == 0:
                self._index += 1
                return self._item
            else:
                raise StopIteration

    def __init__(self, id, start_location = None, end_location = None, state = TRACK_NORMAL, normal_color = None, safe_color = None, danger_color = None):
        self.id = id
        if normal_color is None:
            normal_color = STUB_NORMAL_COLOR
        if safe_color is None:
            safe_color = STUB_SAFE_COLOR
        if danger_color is None:
            danger_color = STUB_DANGER_COLOR
        self.track = Track('Track-' + id, start_location, end_location, state, normal_color, safe_color, danger_color)

    def __iter__(self):
        return self._Iterator(self)

    def get_start_location(self):
        return self.track.get_start_location()
    
    def get_end_location(self):
        return self.get_end_location()

    def set_panel(self, panel):
        self.track.set_panel(panel)

    def draw(self):
        self.track.draw()

    def clicked(self, figures):
        pass

    def erase(self):
        self.track.erase()

class Signal:
    class _Iterator:
        def __init__(self, item):
            self._item = item
            self._index = 0

        def __next__(self):
            if self._index == 0:
                self._index += 1
                return self._item
            else:
                raise StopIteration

    def __init__(self, id, location, state = SIGNAL_DANGER, clear_color = None, danger_color = None, inform = None, respond = None, gui_button = None, push_button = None, keyboard_event = None, supervisor = None, wait_for_set = None):
        self.id = id
        self.location = location
        self.state = state
        if clear_color is None:
            self.clear_color = SIGNAL_CLEAR_COLOR
        else:
            self.clear_color = clear_color
        if danger_color is None:
            self.danger_color = SIGNAL_DANGER_COLOR
        else:
            self.danger_color = danger_color
        if gui_button is None:
            self.gui_button = SIGNAL_GUI_BUTTON
        else:
            self.gui_button = gui_button
        if isinstance(push_button, int):
            self.push_button = PushButton(button_id = id, pin_id = push_button, callback = self.toggle)
        elif isinstance(push_button, PushButton):
            self.push_button = push_button
        else:
            self.push_button = None
        if wait_for_set is None:
            self.wait_for_set = SIGNAL_WAIT_FOR_SET
        else:
            self.wait_for_set = wait_for_set
        self.keyboard_event = keyboard_event
        self.supervisor = supervisor
        if self.supervisor:
            if self.supervisor not in _supervisors:
                sv = nw0.discover(self.supervisor)
                if sv is None:
                    sg.popup_error('Unable to discover supervisor ' + self.supervisor, title = 'No supervisor found')
                    exit()
                else:
                    _supervisors[self.supervisor] = sv
            status = nw0.send_message_to(_supervisors[self.supervisor], 'exists:signal:' + self.id)
            if status != 'ok':
                sg.popup_error("Signal '" + self.id + "' does not exist on Supervisor " + self.supervisor, title = 'Non-existant Signal')
                exit()
        self.inform = inform
        self.respond = respond
        self.graph_id = None
        self.panel = None

    def __iter__(self):
        return self._Iterator()

    def _supervisor_set(self, position):
        if self.supervisor:
            status = nw0.send_message_to(_supervisors[self.supervisor], 'set:signal:' + self.id + ':' + position)
            if status == 'ok':
                while self.wait_for_set:
                    status = nw0.send_message_to(_supervisors[self.supervisor], 'status:signal:' + self.id)
                    response = status.split(':')
                    if response[0] == 'set':
                        break
                    elif response[0] == 'moving':
                        continue
                    else:
                        sg.popup_error(status, 'Error getting status of signal ' + self.id, title = 'Status error')
                        return False
                return True
            else:
                sg.popup_error(status, 'Error setting signal ' + self.id + ' to ' + position, title = 'Error setting signal')
                return False
        else:
            return True

    def set_supervisor_state(self):
        if self.supervisor:
            if self.state == SIGNAL_DANGER:
                self.danger()
            elif self.state == SIGNAL_CLEAR:
                self.clear()

    def clear(self):
        if self._supervisor_set('clear'):
            self.state = SIGNAL_CLEAR
            if self.panel:
                self.panel.tk_canvas.itemconfigure(self.graph_id, fill = self.clear_color, outline = self.clear_color)

    def danger(self):
        if self._supervisor_set('danger'):
            self.state = SIGNAL_DANGER
            if self.panel:
                self.panel.tk_canvas.itemconfigure(self.graph_id, fill = self.danger_color, outline = self.danger_color)

    def toggle(self):
        if self.state == SIGNAL_CLEAR:
            self.danger()
        elif self.state == SIGNAL_DANGER:
            self.clear()

    def set_panel(self, panel):
        self.panel = panel

    def draw(self):
        if self.location:
            if self.state == SIGNAL_DANGER:
                color = self.danger_color
            elif self.state == SIGNAL_CLEAR:
                color = self.clear_color
            else:
                color = self.danger_color
            if self.panel:
                self.graph_id = self.panel.draw_circle(self.location, 10, fill_color = color, line_color = color)

    def clicked(self, figures):
        if self.graph_id in figures:
            self.toggle()

    def erase(self):
        if self.panel:
            self.panel.delete_figure(self.graph_id)

class Turnout:
    class _Iterator:
        def __init__(self, item):
            self._item = item
            self._index = 0

        def __next__(self):
            if self._index == 0:
                self._index += 1
                return self._item
            else:
                raise StopIteration

    def __init__(self, id, location, entry = None, normal = None, reverse = None, normal_color = None, safe_color = None, danger_color = None, point_color = None, inform = None, respond = None, gui_button = None, push_button = None, keyboard_event = None, supervisor = None, wait_for_set = None):
        self.id = id
        self.location = location
        if normal_color is None:
            normal_color = TURNOUT_NORMAL_COLOR
        if safe_color is None:
            safe_color = TURNOUT_SAFE_COLOR
        if danger_color is None:
            danger_color = TURNOUT_DANGER_COLOR
        if entry:
            self.entry_location = entry
        else:
            self.entry_location = (self.location[0] - 100, self.location[1])
        self.entry_track = Track('Track-Entry-' + id, location, self.entry_location, TRACK_NORMAL, normal_color, safe_color, danger_color)
        if normal:
            self.normal_location = normal
        else:
            self.normal_location = (self.location[0] + 100, self.location[1])
        self.normal_track = Track('Track-Normal-' + id, location, self.normal_location, TRACK_SAFE, normal_color, safe_color, danger_color)
        if reverse:
            self.reverse_location = reverse
        else:
            self.reverse_location = (self.location[0] + 100, self.location[1] - 50)
        self.reverse_track = Track('Track-Reverse-' + id, location, self.reverse_location, TRACK_DANGER, normal_color, safe_color, danger_color)
        if point_color is None:
            self.point_color = TURNOUT_POINT_COLOR
        else:
            self.point_color = point_color
        if gui_button is None:
            self.gui_button = TURNOUT_GUI_BUTTON
        else:
            self.gui_button = gui_button
        if isinstance(push_button, int):
            self.push_button = PushButton(button_id = id, pin_id = push_button, callback = self.toggle)
        elif isinstance(push_button, PushButton):
            self.push_button = push_button
        else:
            self.push_button = None
        if wait_for_set is None:
            self.wait_for_set = TURNOUT_WAIT_FOR_SET
        else:
            self.wait_for_set = wait_for_set
        self.keyboard_event = keyboard_event
        self.supervisor = supervisor
        if self.supervisor:
            if self.supervisor not in _supervisors:
                sv = nw0.discover(self.supervisor)
                if sv is None:
                    sg.popup_error('Unable to discover supervisor ' + self.supervisor, title = 'No supervisor found')
                    exit()
                else:
                    _supervisors[self.supervisor] = sv
            status = nw0.send_message_to(_supervisors[self.supervisor], 'exists:turnout:' + self.id)
            if status != 'ok':
                sg.popup_error("Turnout '" + self.id + "' does not exist on Supervisor " + self.supervisor, title = 'Non-existant turnout')
                exit()
        self.inform = inform
        self.respond = respond
        self.point_circle_graph_id = None
        self.state = 'N'
        self.panel = None

    def __iter__(self):
        return self._Iterator()
    
    def _supervisor_set(self, position):
        if self.supervisor:
            self.normal_track.danger()
            self.reverse_track.danger()
            self.state = 'I' # Indeterminate
            status = nw0.send_message_to(_supervisors[self.supervisor], 'set:turnout:' + self.id + ':' + position)
            if status == 'ok':
                while self.wait_for_set:
                    status = nw0.send_message_to(_supervisors[self.supervisor], 'status:turnout:' + self.id)
                    response = status.split(':')
                    if response[0] == 'set':
                        break
                    elif response[0] == 'moving':
                        continue
                    else:
                        sg.popup_error(status, 'Error getting status of turnout ' + self.id, title = 'Status error')
                        return False
                return True
            else:
                sg.popup_error(status, 'Error setting turnout ' + self.id + ' to ' + position, title = 'Error setting turnout')
                return False
        else:
            return True
    
    def set_supervisor_state(self):
        if self.supervisor:
            if self.state == 'N':
                self.normal()
            elif self.state == 'R':
                self.reverse()

    def get_entry_location(self):
        return self.entry_location

    def get_normal_location(self):
        return self.normal_location

    def get_reverse_location(self):
        return self.reverse_location

    def normal(self):
        if self._supervisor_set('normal'):
            self.normal_track.safe()
            self.reverse_track.danger()
            self.state = 'N'

    def reverse(self):
        if self._supervisor_set('reverse'):
            self.normal_track.danger()
            self.reverse_track.safe()
            self.state = 'R'

    def toggle(self):
        if self.state == 'R':
            self.normal()
        elif self.state == 'N':
            self.reverse()

    def set_panel(self, panel):
        self.panel = panel
        self.entry_track.set_panel(panel)
        self.normal_track.set_panel(panel)
        self.reverse_track.set_panel(panel)

    def draw(self):
        self.entry_track.draw()
        self.normal_track.draw()
        self.reverse_track.draw()
        if self.panel:
            self.point_circle_graph_id = self.panel.draw_circle(self.location, 10, fill_color = self.point_color, line_color = self.point_color)

    def clicked(self, figures):
        if self.point_circle_graph_id in figures or self.entry_track.get_graph_id() in figures or self.normal_track.get_graph_id() in figures or self.reverse_track.get_graph_id() in figures:
            self.toggle()

    def erase(self):
        self.entry_track.erase()
        self.normal_track.erase()
        self.reverse_track.erase()
        if self.panel:
            self.panel.delete_figure(self.point_circle)

class Block:
    class _Iterator:
        def __init__(self, items):
            self._items = items
            self._index = 0

        def __next__(self):
            if self._index < len(self._items):
                result = self._items[self._index]
                self._index += 1
                return result
            else:
                raise StopIteration

    def __init__(self, id, label = None, label_location = None, label_font_size = 20, label_color = None):
        self.id = id
        self.label = label
        self.label_location = label_location
        self.label_font_size = label_font_size
        if label_color is None:
            self.label_color = BLOCK_LABEL_COLOR
        else:
            self.label_color = label_color
        self.items = []
        self.panel = None

    def __iter__(self):
        return self._Iterator(self.items)

    def __getitem__(self, key):
        print('__getitem__() key:', key)
        return self.find_element(key)

    def find_element(self, key):
        for item in self.items:
            if item.id == key:
                return item
        raise KeyError(key)

    def add(self, item):
        if isinstance(item, (Block, Track, Stub, Turnout, Signal)):
            self.items.append(item)
        else:
            raise TypeError(f'Attempt to add a \'{type(item).__name__}\' to a block. Valid types are Block, Track, Stub, Turnout or Signal. Revise your code so that one of the correct types is added')

    def set_panel(self, panel):
        self.panel = panel
        for item in self.items:
            item.set_panel(panel)

    def draw(self):
        if self.label and self.panel:
            self.panel.draw_text(self.label, self.label_location, color = self.label_color, font = ('', self.label_font_size))
        for item in self.items:
            item.draw()

    def clicked(self, figures):
        for item in self.items:
            item.clicked(figures)

    def erase(self):
        for item in self.items:
            item.erase()

class Layout:
    def __init__(self, label, label_font_size = 30, label_color = None, background_color = None, height = 300, width = 1200, clickable_panel = True, item_buttons = True, route_buttons = True, exit_button = True, informers = False, responders = False):
        self.label = label
        self.label_font_size = label_font_size
        if label_color is None:
            self.label_color = LAYOUT_LABEL_COLOR
        else:
            self.label_color = label_color
        if background_color is None:
            self.background_color = LAYOUT_BACKGROUND_COLOR
        else:
            self.background_color = background_color
        self.width = width
        self.height = height
        self.item_buttons = item_buttons
        self.route_buttons = route_buttons
        self.exit_button = exit_button
        self.clickable_panel = clickable_panel
        self.blocks = []
        self.routes = []
        self.panel = None

    def add_block(self, block):
        if isinstance(block, (Block, Track, Stub, Turnout, Signal)):
            self.blocks.append(block)
        else:
            raise TypeError(f'Attempt to add a \'{type(block).__name__}\' to the block list. Valid types are Block, Track, Stub, Turnout or Signal. Revise your code so that one of the correct types is added')

    def add_route(self, route):
        if isinstance(route, Route):
            self.routes.append(route)
        else:
            raise TypeError(f'Attempt to add a \'{type(route).__name__}\' to the Route list, revise your code so that the correct type is added')

    def add(self, item):
        if isinstance(item, (Route, Block, Track, Stub, Turnout, Signal)):
            if isinstance(item, Route):
                self.add_route(item)
            else:
                self.add_block(item)
        else:
            raise TypeError(f'Attempt to add a \'{type(item).__name__}\' to a layout. Valid types are Route, Block, Track, Stub, Turnout or Signal. Revise your code so that one of the correct types is added')
    
    def _make_block_buttons(blocks, block_buttons):
        for block in blocks:
            if isinstance(block, Block):
                Layout._make_block_buttons(block, block_buttons)
            elif (isinstance(block, Turnout) or isinstance(block, Signal)) and block.gui_button:
                block_buttons.append(sg.Button(block.id, font = ('', 20), key = '+item+' + block.id))
    
    def _make_block_keyboard_events(blocks, events):
        for block in blocks:
            if isinstance(block, Block):
                Layout._make_block_keyboard_events(block, events)
            elif (isinstance(block, Turnout) or isinstance(block, Signal)) and block.keyboard_event:
                events[block.keyboard_event] = block.toggle
    
    def _update_supervisors(blocks):
        for block in blocks:
            if isinstance(block, Block):
                Layout._update_supervisors(block)
            elif isinstance(block, Turnout) or isinstance(block, Signal):
                block.set_supervisor_state()

    def run(self, initial_route = None, full_screen = True, headless = False, enable_keyboard = False, close_all_supervisors = True):
        keyboard_events = {}
        
        if enable_keyboard:
            Layout._make_block_keyboard_events(self.blocks, keyboard_events)
            for route in self.routes:
                if route.keyboard_event:
                    keyboard_events[route.keyboard_event] = route.run

        if headless:
            # initial_route can be either a Route or a string ID of a route
            if initial_route:
                if isinstance(initial_route, Route):
                    initial_route.run()
                else:
                    for route in self.routes:
                        if route.id == initial_route:
                            route.run()
                            break
            
            # At this stage everything is ready so make sure all supervisors are in step
            Layout._update_supervisors(self.blocks)

            # Need to pause here so that push buttons and whatever else can be processed until shutdown
            print('Running ' + self.label + ', press enter to quit...')
            while True:
                event = getkey()
                print('event', event)
                if event == keys.ENTER:
                    break
                else:
                    for keyboard_event in keyboard_events:
                        if keyboard_event == event:
                            keyboard_events[keyboard_event]()
                            break
        else:
            screen_size = _get_screen_size()
            canvas_size = (screen_size[0] - 100, screen_size[1] - 250)

            sg.theme(APPLICATION_THEME)

            buttons = []
            if self.item_buttons:
                block_buttons = []
                Layout._make_block_buttons(self.blocks, block_buttons)
                if len(block_buttons):
                    buttons.append(block_buttons)

            if self.route_buttons:
                route_buttons = []
                for route in self.routes:
                    if route.gui_button:
                        route_buttons.append(sg.Button(route.id, font = ('', 20), key = '+route+' + route.id))
                if len(route_buttons):
                    buttons.append(route_buttons)
            if self.exit_button:
                buttons.append([sg.Button('Exit', font = ('', 20))])

            layout = [ [sg.Text(self.label, font = ('', self.label_font_size), justification = 'center', expand_x = True)],
                    [sg.Graph(canvas_size = canvas_size, graph_bottom_left = (0, 0), graph_top_right = (self.width, self.height), background_color = self.background_color, enable_events = True, key = 'panel', expand_x = True)] ]
            if self.item_buttons or self.route_buttons or self.exit_button:
                layout.append([sg.Column(buttons, expand_x = True, element_justification = 'center')])

            window = sg.Window('Layout Control Lite', layout, size = screen_size, finalize = True, no_titlebar = full_screen, return_keyboard_events = enable_keyboard)

            panel = window['panel']

            for block in self.blocks:
                block.set_panel(panel)

            for block in self.blocks:
                block.draw()

            # initial_route can be either a Route or a string ID of a route
            if initial_route:
                if isinstance(initial_route, Route):
                    initial_route.run()
                else:
                    for route in self.routes:
                        if route.id == initial_route:
                            route.run()
                            break
            
            # At this stage everything is ready to display on the screen, so make sure all supervisors
            # are in step with what we are about to show
            Layout._update_supervisors(self.blocks)

            while True:
                event, values = window.read()
                if event == sg.WIN_CLOSED:
                    break
                if event == 'Exit':
                    break
                if event == 'panel' and self.clickable_panel:
                    figures = window['panel'].get_figures_at_location(values['panel'])
                    if len(figures):
                        for block in self.blocks:
                            block.clicked(figures)
                else:
                    if event.startswith('+route+'):
                        route_id = event[7:]
                        for route in self.routes:
                            if route.id == route_id:
                                route.run()
                                break
                    elif event.startswith('+item+'):
                        item_id = event[6:]
                        done = False
                        for block in self.blocks:
                            if isinstance(block, Turnout) or isinstance(block, Signal):
                                if block.id == item_id:
                                    block.toggle()
                                    done = True
                            else:
                                for item in block:
                                    if item.id == item_id:
                                        item.toggle()
                                        done = True
                            if done:
                                break
                    else:
                        # On a Raspberry Pi we get event.keysym and event.keycode rather than event.char from
                        # the underlaying tkinter event, this is normalised to a single keyboard character if
                        # we are not given a single keyboard character
                        if len(event) == 1:
                            kb_char = event
                        elif len(event) >= 3 and event[1:2] == ':':
                            kb_char = event[0:1]
                        else:
                            kb_char = ''
                        for keyboard_event in keyboard_events:
                            if keyboard_event == kb_char:
                                keyboard_events[keyboard_event]()
                                break
            window.close()

        if close_all_supervisors:
            for supervisor in _supervisors:
                nw0.send_message_to(_supervisors[supervisor], 'shutdown')

    def __getitem__(self, key):
        return self.find_element(key)

    def find_element(self, key):
        for block in self.blocks:
            if block.id == key:
                return block
        raise KeyError(key)

    def draw(self):
        for block in self.blocks:
            block.draw()

def Main():
    # from LayoutControlLite import Track, Stub, Turnout, Signal, Block, Route, Layout, set_default

#    set_default('LAYOUT_BACKGROUND_COLOR', 'black')

    west_entry_track = Track('West Entry', (25, 200), (75, 200))
    starter_signal = Signal('Starter', (75, 225))
    west_turnout = Turnout('West Turnout', location = (150, 200))

    east_turnout = Turnout('East Turnout', location = (1050, 200), entry = (1150, 200), normal = (950, 200), reverse = (950, 150))
    platform_track = Track('Platform Track', west_turnout.get_normal_location(), east_turnout.get_normal_location())

    platform = Block('Platform', 'Platform', (600, 250))
    platform.add(west_entry_track)
    platform.add(starter_signal)
    platform.add(west_turnout)
    platform.add(east_turnout)
    platform.add(platform_track)

    south_turnout = Turnout('South Turnout', location = (600, 150))
    south_west_track = Track('South West Track', west_turnout.get_reverse_location(), south_turnout.get_entry_location())
    south_east_track = Track('South East Track', east_turnout.get_reverse_location(), south_turnout.get_normal_location())

    loop = Block('Loop', 'Goods Yard Loop', (600, 175))
    loop.add(south_turnout)
    loop.add(south_west_track)
    loop.add(south_east_track)

    goods_yard = Block('Goods Yard', 'Goods Yard', (1100, 125))
    goods_terminus = Stub('Goods Shed Track', south_turnout.get_reverse_location(), (1100, 75))
    goods_yard.add(goods_terminus)

    start_of_day = Route('Start of Day')
    start_of_day.add(starter_signal, 'danger')
    start_of_day.add(east_turnout, 'normal')
    start_of_day.add(west_turnout, 'normal')
    start_of_day.add(south_turnout, 'normal')

    main_line_to_platform = Route('Main Line to Platform')
    main_line_to_platform.add(starter_signal, 'danger')
    main_line_to_platform.add(west_turnout, 'normal')
    main_line_to_platform.add(east_turnout, 'normal')

    main_line_from_platform = Route('Main Line from Platform')
    main_line_from_platform.add(west_turnout, 'normal')
    main_line_from_platform.add(east_turnout, 'normal')
    main_line_from_platform.add(starter_signal, 'clear')

    loop_line = Route('Loop Line')
    loop_line.add(starter_signal, 'danger')
    loop_line.add(west_turnout, 'reverse')
    loop_line.add(east_turnout, 'reverse')
    loop_line.add(south_turnout, 'normal')

    goods_line = Route('Goods Line')
    goods_line.add(starter_signal, 'danger')
    goods_line.add(south_turnout, 'reverse')
    goods_line.add(west_turnout, 'reverse')

    layout = Layout('Simple Test Layout')
    layout.add(platform)
    layout.add(loop)
    layout.add(goods_yard)
    layout.add(start_of_day)
    layout.add(main_line_to_platform)
    layout.add(main_line_from_platform)
    layout.add(loop_line)
    layout.add(goods_line)

    layout.run()

if __name__ == '__main__':
    Main()