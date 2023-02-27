import networkzero as nw0
from time import sleep, time as ticks_ms
try:
    from adafruit_servokit import ServoKit
except:
    class Servo:
        def __init__(self, channel):
            self.channel = channel
            self.angle = 0

    class ServoKit:
        def __init__(self, channels = 16):
            print('Pseudo ServoKit:', channels, 'channels')
            self.channels = channels
            self.servo = []
            for ndx in range(self.channels):
                self.servo.append(Servo(ndx))

class Turnout:
    MAX_THROW = 45
    
    def __init__(self, id, channel, left_max = 35, right_max = 35, move_speed = 30, set_to = 'c', invert = False):
        self.id = id
        self.channel = channel
        self.servo = None
        if left_max > self.MAX_THROW:
            self.left_max = -self.MAX_THROW
        elif left_max < 0:
            self.left_max = 0
        else:
            self.left_max = -left_max
            
        if right_max > self.MAX_THROW:
            self.right_max = self.MAX_THROW
        elif right_max < 0:
            self.right_max = 0
        else:
            self.right_max = right_max
        
        self.move_speed = move_speed # Degrees per second
        
        self.move_start_ms = 0
        self.current_position = 0
        self.start_position = 0
        self.target_position = 0
        self.init_set_to = set_to
        self.invert = invert
        self.set_target_throw(set_to)
        self.direction = 0

    def _move_to(self, position):
        self.current_position = position
        # If the degree position needs to be inverted because of what the Servo
        # thinks of as left and right are the opposite of how we want the tracks
        # from the turnout to run
        degree = position
        if self.invert:
            degree *= -1
        self.servo.angle = degree + 90.0
    
    def initial_position(self):
        self.current_position = self.target_position
        self.direction = 0
        self._move_to(self.current_position)

    def throw_left(self):
        self.set_target_throw('l')
        
    def throw_right(self):
        self.set_target_throw('r')
        
    def center(self):
        self.set_target_throw('c')
    
    # The normal and reverse settings of the points model the way points are
    # thought of in the real world, normal is straight on and reverse is a
    # turn off. The arbitrary decision was made for the throw left to be
    # straight on and throw right to be reverse because 'right' and 'reverse'
    # both have an initial 'r' and 'r' also looks a bit like a a set of
    # points with the branch to the right
    def normal(self):
        self.throw_left()
    
    def reverse(self):
        self.throw_right()

    def is_moving_to_target(self):
        return self.direction != 0
    
    def is_on_target(self):
        return not self.is_moving_to_target()
    
    def is_active(self):
        return self.is_moving_to_target()

    def is_passive(self):
        return not self.is_active()

    def set_target_throw(self, hand):
        h = hand.lower()
        if h == 'r':
            self.set_target(self.right_max)
        elif h == 'l':
            self.set_target(self.left_max)
        elif h == 'c':
            self.set_target((self.right_max + self.left_max) / 2.0)

    def set_target(self, target):
        if self.current_position != target:
            self.start_position = self.current_position
            self.target_position = target
            self.move_start_ms = ticks_ms()
            if self.target_position < self.current_position:
                self.direction = -1
            else:
                self.direction = 1

    def update(self):
        if self.direction:
            t = ticks_ms() - self.move_start_ms
            next_position = self.start_position + (self.move_speed * t * self.direction)
            if self.direction > 0:
                if next_position > self.target_position:
                    next_position = self.target_position
            else:
                if next_position < self.target_position:
                    next_position = self.target_position
            
            self._move_to(next_position)
            
            if self.target_position == self.current_position:
                # Reached target so indicate stopping movement by setting direction to zero
                self.direction = 0

class Signal:
    MAX_DOWN = 90
    MIN_DOWN = 45
    MAX_LIFT = 135
    MIN_LIFT = 90
    LIFT_BOUNCES = 2
    DROP_BOUNCES = 4
    
    def __init__(self, id, channel, danger_position = 45, clear_position = 90, drop_speed = -75, lift_speed = 25, bounce = True, set_to = '-'):
        self.id = id
        self.channel = channel
        self.servo = None

        if danger_position > clear_position:
            danger_position, clear_position = (clear_position, danger_position)

        if danger_position > self.MAX_DOWN:
            self.danger_position = self.MAX_DOWN
        elif danger_position < self.MIN_DOWN:
            self.danger_position = self.MIN_DOWN
        else:
            self.danger_position = danger_position
        
        if clear_position > self.MAX_LIFT:
            self.clear_position = self.MAX_LIFT
        elif clear_position < self.MIN_LIFT:
            self.clear_position = self.MIN_LIFT
        else:
            self.clear_position = clear_position
        
        if self.clear_position > self.danger_position:
            self.center_position = self.danger_position + ((self.clear_position - self.danger_position) / 2)
        else:
            self.center_position = self.clear_position + ((self.danger_position - self.clear_position) / 2)

        self.lift_speed = lift_speed # Degrees per second
        self.drop_speed = drop_speed
        self.bounce = bounce
        self.targets = []
        self.target_ndx = 0
        self.lift_targets = []
        self.drop_targets = []
        if self.bounce:
            for ndx in range(Signal.LIFT_BOUNCES + 1):
                self.lift_targets.append(self.clear_position)
                self.lift_targets.append(self.clear_position - (self.lift_speed * (Signal.LIFT_BOUNCES - ndx) / 12.5))
            for ndx in range(Signal.DROP_BOUNCES + 1):
                self.drop_targets.append(self.danger_position)
                self.drop_targets.append(self.danger_position - (self.drop_speed * (Signal.DROP_BOUNCES - ndx) / 25.0))
        else:
            self.lift_targets.append(self.clear_position)
            self.drop_targets.append(self.danger_position)
        
        self.move_start_ms = 0
        self.current_position = 0
        self.start_position = 0
        self.target_position = 0
        self.requested_position = ''
        self.init_set_to = set_to
        self.set_target_position(set_to)
        self.direction = 0
    
    def _move_to(self, position):
        self.current_position = position
        self.servo.angle = position
    
    def initial_position(self):
        self.current_position = self.target_position
        self.direction = 0
        self._move_to(self.current_position)

    def danger(self):
        self.requested_position = 'danger'
        self.targets = self.drop_targets
        self.target_ndx = 0
        self.set_target(self.targets[self.target_ndx])
    
    def clear(self):
        self.requested_position = 'clear'
        self.targets = self.lift_targets
        self.target_ndx = 0
        self.set_target(self.targets[self.target_ndx])

    def center(self):
        self.requested_position = 'center'
        self.targets = None
        self.set_target(self.center_position)

    def update(self):
        if self.direction:
            t = ticks_ms() - self.move_start_ms
            if self.direction < 0:
                next_position = self.start_position + (self.drop_speed * t)
                if next_position < self.target_position:
                    next_position = self.target_position
            else:
                next_position = self.start_position + (self.lift_speed * t)
                if next_position > self.target_position:
                    next_position = self.target_position
            
            self._move_to(next_position)
            
            if self.target_position == self.current_position:
                # Reached target, if bouncing then set next bounce target
                if self.targets and self.target_ndx < len(self.targets) - 1:
                    self.target_ndx += 1
                    self.set_target(self.targets[self.target_ndx])
                else:
                    # Reached target so indicate stopping movement by setting direction to zero
                    self.direction = 0
            
    def is_moving_to_target(self):
        return self.direction != 0

    def is_on_target(self):
        return not self.is_moving_to_target()

    def is_active(self):
        return self.is_moving_to_target()
    
    def is_passive(self):
        return not self.is_active()

    def set_target_position(self, flag):
        f = flag.lower()
        if f == 'd':
            self.set_target(self.danger_position)
        elif f == 'c':
            self.set_target(self.clear_position)
        elif f == '-':
            self.set_target(self.center_position)

    def set_target(self, target):
        if self.current_position != target:
            self.start_position = self.current_position
            self.target_position = target
            self.move_start_ms = ticks_ms()
            if self.target_position < self.current_position:
                self.direction = -1
            else:
                self.direction = 1

class Supervisor:
    def __init__(self, id, channels = 16):
        self.id = id
        self.turnouts = {}
        self.signals = {}
        self.kit = ServoKit(channels = channels)

    def reply(self, address, status):
        nw0.send_reply_to(address, status)
    
    def reply_ok(self, address):
        self.reply(address, 'ok')
    
    def reply_error(self, address):
        self.reply(address, 'error')
    
    def add_turnout(self, turnout):
        # Patch up the turnout so that it can move itself
        turnout.servo = self.kit.servo[turnout.channel]
        turnout.initial_position()
        self.turnouts[turnout.id] = turnout
    
    def add_signal(self, signal):
        # Patch up the signal so that it can move itself
        signal.servo = self.kit.servo[signal.channel]
        signal.initial_position()
        self.signals[signal.id] = signal
    
    def run(self):
        address = nw0.advertise(self.id)

        while True:
            message = nw0.wait_for_message_from(address, wait_for_s = 0.01)
            if message is not None:
                print('Got:', message)
                command = message.split(':')
                print(command)
                if command[0] == 'set':
                    if command[1] == 'turnout':
                        if command[2] in self.turnouts:
                            if command[3] in ('normal', 'reverse'):
                                if command[3] == 'normal':
                                    self.turnouts[command[2]].normal()
                                elif command[3] == 'reverse':
                                    self.turnouts[command[2]].reverse()
                                self.reply_ok(address)
                            else:
                                self.reply_error(address)
                        else:
                            self.reply_error(address)
                    elif command[1] == 'signal':
                        if command[2] in self.signals:
                            if command[3] in ('clear', 'danger'):
                                if command[3] == 'clear':
                                    self.signals[command[2]].clear()
                                elif command[3] == 'danger':
                                    self.signals[command[2]].danger()
                                self.reply_ok(address)
                            else:
                                self.reply_error(address)
                        else:
                            self.reply_error(address)
                    else:
                        self.reply_error(address)
                elif command[0] == 'status':
                    if command[1] == 'turnout':
                        if command[2] in self.turnouts:
                            self.turnouts[command[2]].counter += 1
                            if self.turnouts[command[2]].counter < 70:
                                status = 'moving:' + str(self.turnouts[command[2]].counter)
                                self.kit.servo[self.turnouts[command[2]].channel].angle = 55.0 + self.turnouts[command[2]].counter
                            else:
                                status = 'set'
                            self.reply(address, status)
                        else:
                            self.reply_error(address)
                    elif command[1] == 'signal':
                        if command[2] in self.signals:
                            self.signals[command[2]].counter += 1
                            if self.signals[command[2]].counter < 70:
                                status = 'moving:' + str(self.signals[command[2]].counter)
                                self.kit.servo[self.signals[command[2]].channel].angle = 55.0 + self.turnouts[command[2]].counter
                            else:
                                status = 'set'
                            self.reply(address, status)
                    else:
                        self.reply_error(address)
                elif command[0] == 'exists':
                    if command[1] == 'turnout':
                        if command[2] in self.turnouts:
                            self.reply_ok(address)
                        else:
                            self.reply_error(address)
                    elif command[1] == 'signal':
                        if command[2] in self.signals:
                            self.reply_ok(address)
                        else:
                            self.reply_error(address)
                    else:
                        self.reply_error(address)
                elif command[0] == 'shutdown':
                    self.reply(address, 'bye')
                    break
                else:
                    self.reply_error(address)
            for signal in self.signals:
                if self.signals[signal].is_active():
                    self.signals[signal].update()
            for turnout in self.turnouts:
                if self.turnouts[turnout].is_active():
                    self.turnouts[turnout].update()

def Main():
#    from LayoutControlLite import Supervisor
#    from LayoutControlLite.Supervisor import Turnout, Signal

    west = Turnout(id = 'West Turnout', channel = 0)
    east = Turnout(id = 'East Turnout', channel = 1)
    south = Turnout(id = 'South Turnout', channel = 2)

    starter = Signal(id = 'Starter', channel = 3)

    supervisor = Supervisor('servo_manager')
    supervisor.add_turnout(west)
    supervisor.add_turnout(east)
    supervisor.add_turnout(south)
    supervisor.add_signal(starter)

    supervisor.run()    

if __name__ == '__main__':
    Main()