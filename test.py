#!/usr/bin/env python3
# This script prints the full content of timetravel.mcfunction with support for 64 loops.
print("execute if score loop timers matches 1.. run scoreboard players add loop timers 1")
print("execute if score loop timers matches 0 run mocap recording start @a")
print("execute if score loop timers matches 0 run scoreboard players set loop timers 1")
print("execute if score loop timers matches 6000.. run mocap recording stop")
print("execute if score loop timers matches 6000.. run mocap playing stopAll")
for i in range(64):
    # For loopCount = i, the new recording will be saved as loop(i+1)
    loopName = "loop" + str(i+1)
    print("execute if score loop timers matches 6000.. if score loopCount activators matches " + str(i) + " run mocap recording save " + loopName)
    for j in range(i+1):
        # For each already saved loop from 1 to (i+1)
        print("execute if score loop timers matches 6000.. if score loopCount activators matches " + str(i) + " run mocap playing start loop" + str(j+1))
print("execute if score loop timers matches 6000.. run scoreboard players add loopCount activators 1")
print("execute if score loop timers matches 6000.. run scoreboard players set loop timers 0")
