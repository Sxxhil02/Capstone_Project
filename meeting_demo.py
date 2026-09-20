"""
-----------------------------------------------------------------------
Each beat opens one window. Close that window
to move on to the next beat. Nothing to type, nothing to switch
between -- just run, talk, close, repeat.

  Beat 1 -- Preference alone changes the recommendation
      (outer_routing_demo.py: slider + radio buttons)

  Beat 2 -- Ignoring congestion makes that advice measurably wrong
      (congestion_distortion_demo.py: slider)

  Beat 3 -- A naive fix doesn't stabilise; a standard one does
      (iterated_congestion_loop.py: sliders + damping-scheme choice)
"""

import matplotlib.pyplot as plt

print("=" * 72)
print("BEAT 1 -- Does an attendee's own preference change the advice?")
print("-" * 72)
print("Drag the w_time slider from 0 (fare-focused) to 1 (time-focused).")
print("Watch the recommended gate (red) and the ranking in the title flip.")
print("Try the radio buttons too -- different attendees flip differently.")
print("Close this window to continue to Beat 2.")
print("=" * 72)

import outer_routing_demo
outer_routing_demo.build_figure()  # blocks until the window is closed


print()
print("=" * 72)
print("BEAT 2 -- How wrong is advice that ignores congestion?")
print("-" * 72)
print("Drag k up from 0. Watch load shift away from previously-popular")
print("gates (middle panel) and the regret histogram spread out (right).")
print("At k=0, naive and aware are identical -- that's the sanity check.")
print("Close this window to continue to Beat 3.")
print("=" * 72)

import congestion_distortion_demo
plt.show()  # shows the figure congestion_distortion_demo already built


print()
print("=" * 72)
print("BEAT 3 -- Does a fix for that actually work reliably?")
print("-" * 72)
print("Leave alpha at 1.0 with 'Constant alpha' selected first --")
print("watch the left panel oscillate forever between gates, and the")
print("right panel plateau at a large, non-zero value.")
print("Then click 'MSA (1/n)' -- watch it settle down smoothly instead,")
print("and the right panel trend toward zero.")
print("Close this window when finished.")
print("=" * 72)

import iterated_congestion_loop
plt.show()


print()
print("=" * 72)
print("Done. The story: preferences move the advice; ignoring congestion")
print("makes it measurably wrong; a naive fix doesn't stabilise it, but a")
print("standard traffic-assignment technique (MSA) does.")
print("=" * 72)