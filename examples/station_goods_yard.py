from LayoutControlLite import Track, Stub, Turnout, Signal, Block, Route, Layout

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

layout = Layout('Shaws Halt')
layout.add(platform)
layout.add(loop)
layout.add(goods_yard)
layout.add(start_of_day)
layout.add(main_line_to_platform)
layout.add(main_line_from_platform)
layout.add(loop_line)
layout.add(goods_line)

layout.run()
