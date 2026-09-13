# P7-S04 retarget fix (Blender only)

Result: **P7_CF_ANIM_RETARGET_FIXED_OFFLINE**.

Gun-driven relative retarget. Hands stay on the CS hold grip plus CF hand-vs-gun change.
Not compiled. Not deployed.

| clip | gun-hand min/max (old) | gun-hand min/max (new) | mag travel | wrist max Δ |
|---|---|---|---|---|
| reload | 3.76/32.48 | 4.24/12.10 | 9.42 | 0.00 |
| draw | 4.69/24.17 | 2.81/5.68 | 1.73 | 0.00 |
| idle | 4.69/4.69 | 4.69/4.69 | 0.00 | 0.00 |
| shoot1 | 4.69/4.69 | 4.69/4.69 | 1.59 | 0.00 |

Gates: `{"frame0_stays_on_p6_hold": true, "gun_hand_relative_stable": true, "reload_mag_moves": true, "wrist_length_stable": true, "finger_length_stable": true}`
