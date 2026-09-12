# N05-D — PV LTB/UV binding diagnostic and named cube

Result: **MESH_UV_AND_CUBE_RECOVERED_BINDING_OPEN**. P4-M01 remains **INCOMPLETE**.

PV LTB, RS and DTX were re-read through the N05-C verified resolver. QV copies are retained and were not wrapped onto the PV mesh. Filename similarity is not used as binding proof.

## PV LTB

- payload SHA256: `5dbcee45c4565b2026a4e4d2d639a4b7022b4f4fc1c5ef69bc8f49fd5a6c54f7`
- meshes: 11  vertices: 4926  triangles: 5342

| Piece | Kind | Tris | Has UV | UV min | UV max | Outside 0–1 |
|---|---|---:|---|---|---|---:|
| `Fview-hand2` | hands | 1060 | True | [0.0062060002237558365, 0.030285000801086426] | [0.9882810115814209, 0.9682360291481018] | 0 |
| `Fview-arm2` | hands | 274 | True | [0.012914000079035759, 0.021904999390244484] | [0.9819380044937134, 0.9932379722595215] | 0 |
| `M4A1S_BornBeast` | weapon | 3407 | True | [0.0008520000264979899, 0.0005549999768845737] | [0.9976680278778076, 0.9984949827194214] | 0 |
| `M4A1S_BornBeast04` | weapon | 52 | True | [0.10027699917554855, 0.3777559995651245] | [0.2567810118198395, 0.4637550115585327] | 0 |
| `M4A1S_BornBeast02` | weapon | 121 | True | [0.6055120229721069, 0.5599499940872192] | [0.8857889771461487, 0.7710549831390381] | 0 |
| `M4A1S_BornBeast03` | weapon | 184 | True | [0.3908030092716217, 0.20037099719047546] | [0.9007319808006287, 0.6981040239334106] | 0 |
| `M4A1S_BornBeast07` | weapon | 52 | True | [0.18139199912548065, 0.37752801179885864] | [0.267753005027771, 0.4644159972667694] | 0 |
| `M4A1S_BornBeast08` | weapon | 52 | True | [0.2089339941740036, 0.37784498929977417] | [0.2785309851169586, 0.4643990099430084] | 0 |
| `M4A1S_BornBeast05` | weapon | 52 | True | [0.12800100445747375, 0.3774479925632477] | [0.2690039873123169, 0.4642319977283478] | 0 |
| `M4A1S_BornBeast06` | weapon | 52 | True | [0.15448999404907227, 0.3778490126132965] | [0.2559889853000641, 0.4646250009536743] | 0 |
| `M4A1S_BornBeast01` | weapon | 36 | True | [0.8548640012741089, 0.7060940265655518] | [0.9962400197982788, 0.9959329962730408] | 0 |

## Cube

- `ModelTextures/EnvCubeMap/Black_Shader03.DDS` sha256 `c4954419d59bea55b0f592957eab92fa623583d28158cbf84e95bacd233c4e92` routing `main_file` size 393344, 6 identical copies across rez3–rez6/RF017. First-face PNG preview is 256×256 and nearly black, consistent with the name and with CFG `EnvCubeMapBrightness=4` on a dark cube. Cubemap face layout beyond the first face is not asserted by the thumbnail decoder.

## Native-only UV diagnostic

Overlay samples the verified 1024×1024 PV DTX using UVs from the official OBJ export of the verified PV LTB. Hands and weapon pieces are drawn separately. This checks atlas layout; it is not CFG/FXO runtime proof.

Weapon-piece islands sit on gun body / magazine / serial `M4A1SSQ00083` regions of that atlas. Hand pieces also span most of the 0–1 square on the **same** PV sheet (gloves/arms are not a second texture). That is atlas sharing, not a reason to swap in the QV copy.

- weapon: `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05d_binding_uv_cube/pv_weapon_uv_on_verified_dtx.png` triangles=4008
- hands: `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05d_binding_uv_cube/pv_hands_uv_on_verified_dtx.png` triangles=1334
- all: `work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05d_binding_uv_cube/pv_all_uv_on_verified_dtx.png` triangles=5342

## QV copies kept

Main-index QV 256 and any rez2 QV 1024 remain listed. Load order is unknown, so neither was applied to the PV mesh.

## Limitations

- LTB nNumTextures=0: piece table does not name DTX/TGA files.
- CFG Name2 fields are file references, not runtime technique proof.
- UV overlay is a native-only diagnostic of layout on the verified PV atlas.
- OBJ exporter guessed textures are not accepted as binding.
