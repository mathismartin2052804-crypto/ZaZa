-- AnimDragon : anime le dragon v6 importé (Dragon_V6.glb) en pilotant ses os (Bone.Transform).
-- Placement : ModuleScript dans ReplicatedStorage ; à utiliser depuis un LocalScript (rendu fluide côté client)
-- ou un Script serveur. Les deux MeshParts (Dragon, DragonNeon) doivent être dans le même Model que les os.
--   local Anim = require(ReplicatedStorage.AnimDragon)
--   local d = Anim.new(workspace.Dragon_V6)
--   d:play("Course")            -- "Course", "Vol", "Rugissement", "Repos"
--   d:blink()                   -- clignement
--   d:look(20, 5)               -- regard en degrés (+ = vers la droite du dragon, + = vers le haut)
--   d:squint(0.4)               -- plisser les yeux (0 ouverts, 1 fermés)
--   d:setRate(vitesse / Anim.VITESSE_COURSE)   -- cale la foulée sur la vitesse réelle (pieds qui ne patinent pas)
-- Mêmes formules que generateur/demo_animations_v6.py (angles en degrés, ordre YXZ, autour de la tête de chaque os) ;
-- la course vient de generateur/course_v6.py (angles des pattes calculés par IK, copiés dans la table COURSE).
local RunService = game:GetService("RunService")

local Anim = {}
Anim.__index = Anim

local BONES = { "Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "EyelidR", "PupilR", "EyelidL", "PupilL", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "FrontUpperLegR", "FrontLowerLegR", "FrontFootR", "BackUpperLegR", "BackLowerLegR", "BackFootR", "WingUpperR", "WingLowerR", "WingFinger1R", "WingFinger2R", "WingFinger3R", "WingFinger4R", "FrontUpperLegL", "FrontLowerLegL", "FrontFootL", "BackUpperLegL", "BackLowerLegL", "BackFootL", "WingUpperL", "WingLowerL", "WingFinger1L", "WingFinger2L", "WingFinger3L", "WingFinger4L" }
local LID_AXIS = { R = Vector3.new(0.4276, 0.4860, 0.7622), L = Vector3.new(-0.4276, 0.4860, 0.7622) }
local LID_CLOSE = math.rad(100.0)
local PUPIL_AXIS = { R = Vector3.new(0.4905, -0.0000, 0.8714), L = Vector3.new(0.4905, 0.0000, -0.8714) }
local rad, sin, cos, max, abs, clamp = math.rad, math.sin, math.cos, math.max, math.abs, math.clamp
local TAU = 2 * math.pi

-- course : vitesse au sol (studs/s) à donner au dragon pour que ses pieds ne patinent pas à la vitesse normale
Anim.VITESSE_COURSE = 7.273

-- pattes pendant la course (une ligne par échantillon de foulée) : pour avant R, avant L, arrière R, arrière L :
-- haut et bas de la patte (degrés, autour de X) puis pied (quaternion x, y, z, w)
local COURSE = {
	{ -10.1632, 53.5902, -0.7481, 0.0183, 0.0036, 0.6633, -1.9342, 52.3618, -0.8591, 0.0181, 0.0048, 0.5114, 15.2844, -8.1767, 0.0095, -0.0004, -0.0031, 1.0000, 23.1239, -9.7531, -0.1097, -0.0004, -0.0031, 0.9940 },
	{ -11.4122, 54.1303, -0.7522, 0.0184, 0.0032, 0.6587, 5.3810, 48.3220, -0.8977, 0.0181, 0.0045, 0.4401, 14.7933, -6.6020, 0.0029, -0.0035, -0.0039, 1.0000, 21.4860, -10.3941, -0.0920, -0.0033, -0.0041, 0.9957 },
	{ -11.0179, 54.2252, -0.7571, 0.0182, 0.0023, 0.6530, 12.5915, 43.4656, -0.9250, 0.0179, 0.0041, 0.3795, 15.0478, -6.0650, -0.0089, -0.0064, -0.0047, 0.9999, 19.7697, -10.9285, -0.0747, -0.0061, -0.0051, 0.9972 },
	{ -9.1898, 54.1692, -0.7776, 0.0178, 0.0015, 0.6284, 18.7940, 39.2283, -0.9424, 0.0175, 0.0035, 0.3339, 17.3932, -7.3850, -0.0426, -0.0092, -0.0055, 0.9990, 17.9745, -11.3506, -0.0577, -0.0087, -0.0062, 0.9983 },
	{ -5.1859, 53.1358, -0.8137, 0.0170, 0.0008, 0.5810, 23.7288, 36.4109, -0.9530, 0.0168, 0.0025, 0.3025, 20.6133, -9.3114, -0.0871, -0.0117, -0.0064, 0.9961, 16.0997, -11.6538, -0.0410, -0.0112, -0.0072, 0.9991 },
	{ 0.9226, 50.3065, -0.8554, 0.0160, 0.0003, 0.5177, 28.0184, 34.1540, -0.9589, 0.0159, 0.0013, 0.2834, 21.9459, -10.1971, -0.1066, -0.0140, -0.0071, 0.9942, 14.1446, -11.8310, -0.0247, -0.0134, -0.0082, 0.9996 },
	{ 8.3192, 45.4928, -0.8920, 0.0147, -0.0001, 0.4518, 32.3670, 31.0920, -0.9610, 0.0147, 0.0002, 0.2762, 20.5003, -10.5613, -0.0933, -0.0161, -0.0078, 0.9955, 12.1089, -11.8744, -0.0087, -0.0154, -0.0091, 0.9998 },
	{ 15.8322, 39.5410, -0.9184, 0.0132, -0.0005, 0.3954, 35.2793, 29.6315, -0.9588, 0.0131, -0.0012, 0.2839, 18.4318, -10.8473, -0.0749, -0.0178, -0.0085, 0.9970, 9.9922, -11.7759, 0.0068, -0.0171, -0.0099, 0.9998 },
	{ 22.4469, 33.9747, -0.9355, 0.0115, -0.0012, 0.3533, 35.4396, 31.7960, -0.9513, 0.0112, -0.0028, 0.3081, 16.3110, -10.9988, -0.0570, -0.0192, -0.0091, 0.9981, 7.7950, -11.5270, 0.0218, -0.0184, -0.0106, 0.9995 },
	{ 27.6594, 30.0159, -0.9458, 0.0096, -0.0020, 0.3247, 32.3276, 37.5857, -0.9353, 0.0089, -0.0043, 0.3537, 14.1454, -11.0161, -0.0397, -0.0203, -0.0096, 0.9990, 5.5179, -11.1193, 0.0364, -0.0195, -0.0111, 0.9991 },
	{ 31.7965, 27.3892, -0.9514, 0.0076, -0.0030, 0.3077, 26.1577, 45.0420, -0.9028, 0.0061, -0.0054, 0.4301, 11.9417, -10.8994, -0.0231, -0.0210, -0.0100, 0.9995, 3.1623, -10.5444, 0.0504, -0.0202, -0.0115, 0.9985 },
	{ 35.9191, 24.1744, -0.9534, 0.0053, -0.0040, 0.3016, 17.9331, 51.0148, -0.8400, 0.0032, -0.0058, 0.5426, 9.7059, -10.6487, -0.0070, -0.0214, -0.0102, 0.9997, 0.7302, -9.7940, 0.0638, -0.0206, -0.0117, 0.9977 },
	{ 38.9646, 22.0644, -0.9514, 0.0029, -0.0048, 0.3080, 9.8722, 52.2403, -0.7331, 0.0005, -0.0056, 0.6801, 7.4432, -10.2637, 0.0083, -0.0214, -0.0102, 0.9997, -1.7763, -8.8604, 0.0764, -0.0207, -0.0116, 0.9968 },
	{ 39.2822, 23.7952, -0.9449, 0.0003, -0.0055, 0.3272, 4.9984, 46.8977, -0.5843, -0.0020, -0.0052, 0.8115, 5.1578, -9.7441, 0.0230, -0.0211, -0.0100, 0.9995, -4.3544, -7.7360, 0.0883, -0.0204, -0.0114, 0.9958 },
	{ 36.2054, 29.8134, -0.9315, -0.0027, -0.0058, 0.3638, 5.0522, 35.6030, -0.4176, -0.0044, -0.0047, 0.9086, 2.8530, -9.0894, 0.0369, -0.0204, -0.0096, 0.9991, -7.0013, -6.4139, 0.0994, -0.0198, -0.0109, 0.9948 },
	{ 29.9728, 38.2195, -0.9039, -0.0057, -0.0054, 0.4277, 9.4635, 20.5388, -0.2620, -0.0066, -0.0042, 0.9650, 0.5313, -8.2986, 0.0501, -0.0194, -0.0090, 0.9985, -9.7141, -4.8874, 0.1096, -0.0189, -0.0102, 0.9937 },
	{ 21.4941, 45.8017, -0.8495, -0.0085, -0.0045, 0.5276, 14.3226, 9.0014, -0.1595, -0.0088, -0.0037, 0.9871, -1.8058, -7.3709, 0.0626, -0.0182, -0.0083, 0.9978, -11.1753, -4.6848, 0.1110, -0.0176, -0.0095, 0.9936 },
	{ 12.6679, 49.0997, -0.7529, -0.0109, -0.0033, 0.6580, 19.8375, -1.7591, -0.0927, -0.0109, -0.0034, 0.9956, -4.1579, -6.3050, 0.0742, -0.0166, -0.0073, 0.9971, -5.4282, -12.0518, 0.0634, -0.0155, -0.0094, 0.9978 },
	{ 6.4255, 45.7549, -0.6105, -0.0129, -0.0024, 0.7919, 25.1551, -11.1640, -0.0530, -0.0127, -0.0032, 0.9985, -6.5251, -5.0994, 0.0851, -0.0148, -0.0062, 0.9962, 8.8047, -24.0541, -0.0735, -0.0131, -0.0093, 0.9972 },
	{ 5.0204, 35.7700, -0.4415, -0.0146, -0.0017, 0.8971, 29.8219, -18.9825, -0.0309, -0.0143, -0.0030, 0.9994, -8.9089, -3.7524, 0.0951, -0.0128, -0.0049, 0.9954, 25.6141, -31.0466, -0.2901, -0.0111, -0.0080, 0.9569 },
	{ 8.4439, 21.0626, -0.2756, -0.0160, -0.0012, 0.9611, 32.0295, -20.6761, -0.0618, -0.0158, -0.0028, 0.9980, -11.3116, -2.2616, 0.1043, -0.0105, -0.0034, 0.9945, 34.8833, -30.2349, -0.4674, -0.0092, -0.0062, 0.8840 },
	{ 13.4604, 7.7894, -0.1526, -0.0171, -0.0008, 0.9881, 33.1242, -20.1320, -0.1053, -0.0170, -0.0025, 0.9943, -13.2884, -1.1629, 0.1101, -0.0082, -0.0019, 0.9939, 35.9089, -28.3237, -0.5272, -0.0073, -0.0041, 0.8497 },
	{ 18.8617, -3.5995, -0.0727, -0.0180, -0.0005, 0.9972, 34.1623, -21.3743, -0.1126, -0.0179, -0.0020, 0.9935, -9.6196, -6.4598, 0.0814, -0.0056, -0.0006, 0.9967, 34.4598, -28.0011, -0.5202, -0.0053, -0.0019, 0.8540 },
	{ 24.1688, -13.5067, -0.0248, -0.0186, -0.0004, 0.9995, 29.6758, -15.4128, -0.1255, -0.0185, -0.0011, 0.9919, 2.7880, -18.5765, -0.0244, -0.0033, 0.0009, 0.9997, 34.6212, -28.0039, -0.5208, -0.0033, 0.0005, 0.8537 },
	{ 28.8410, -21.8126, 0.0051, -0.0188, -0.0003, 0.9998, 25.5463, -10.4914, -0.1324, -0.0188, -0.0003, 0.9910, 20.1574, -28.3172, -0.2233, -0.0011, 0.0029, 0.9748, 35.6322, -28.4737, -0.5263, -0.0013, 0.0028, 0.8503 },
	{ 30.1396, -22.3735, -0.0222, -0.0188, 0.0001, 0.9996, 21.8430, -6.5130, -0.1349, -0.0188, 0.0005, 0.9907, 32.5503, -29.6325, -0.4241, 0.0010, 0.0051, 0.9056, 37.6062, -29.3676, -0.5380, 0.0008, 0.0051, 0.8430 },
	{ 29.3643, -18.1511, -0.0837, -0.0184, 0.0008, 0.9963, 18.4008, -3.1545, -0.1343, -0.0184, 0.0012, 0.9908, 35.8978, -27.6048, -0.5185, 0.0030, 0.0073, 0.8551, 40.5021, -30.6049, -0.5552, 0.0029, 0.0074, 0.8317 },
	{ 28.9554, -16.0748, -0.1134, -0.0177, 0.0016, 0.9934, 15.1418, -0.2612, -0.1312, -0.0177, 0.0019, 0.9912, 34.7257, -27.1943, -0.5191, 0.0050, 0.0095, 0.8546, 44.1736, -32.0743, -0.5764, 0.0051, 0.0094, 0.8171 },
	{ 25.6633, -11.6120, -0.1241, -0.0167, 0.0025, 0.9921, 12.0244, 2.2522, -0.1260, -0.0167, 0.0025, 0.9919, 35.1577, -27.2543, -0.5205, 0.0069, 0.0114, 0.8537, 48.4061, -33.6374, -0.5994, 0.0072, 0.0113, 0.8003 },
	{ 21.3808, -6.3679, -0.1324, -0.0154, 0.0033, 0.9911, 9.0259, 4.4365, -0.1190, -0.0154, 0.0031, 0.9928, 36.3554, -27.7943, -0.5260, 0.0088, 0.0132, 0.8503, 52.9401, -35.1202, -0.6227, 0.0094, 0.0128, 0.7823 },
	{ 17.5702, -2.0861, -0.1365, -0.0138, 0.0040, 0.9905, 6.1343, 6.3229, -0.1102, -0.0139, 0.0036, 0.9938, 38.4810, -28.7710, -0.5376, 0.0105, 0.0147, 0.8430, 57.4809, -36.2911, -0.6455, 0.0115, 0.0140, 0.7635 },
	{ 14.0712, 1.5466, -0.1376, -0.0119, 0.0046, 0.9904, 3.3446, 7.9309, -0.0999, -0.0121, 0.0042, 0.9949, 41.5244, -30.0964, -0.5551, 0.0122, 0.0159, 0.8315, 61.7028, -36.8309, -0.6684, 0.0136, 0.0148, 0.7436 },
	{ 10.8037, 4.6878, -0.1364, -0.0099, 0.0051, 0.9906, 0.6567, 9.2725, -0.0881, -0.0101, 0.0046, 0.9960, 45.3577, -31.6530, -0.5772, 0.0137, 0.0168, 0.8163, 65.2030, -36.7512, -0.6873, 0.0155, 0.0151, 0.7260 },
	{ 7.7225, 7.4273, -0.1333, -0.0077, 0.0055, 0.9910, -1.9262, 10.3545, -0.0750, -0.0080, 0.0050, 0.9971, 49.7747, -33.3010, -0.6017, 0.0150, 0.0173, 0.7984, 67.6430, -36.9722, -0.6881, 0.0172, 0.0151, 0.7252 },
	{ 4.8005, 9.8202, -0.1286, -0.0054, 0.0058, 0.9917, -4.3984, 11.1804, -0.0605, -0.0058, 0.0054, 0.9981, 54.5174, -34.8740, -0.6269, 0.0163, 0.0173, 0.7787, 68.7151, -38.0324, -0.6613, 0.0186, 0.0148, 0.7497 },
	{ 2.0211, 11.9015, -0.1223, -0.0030, 0.0060, 0.9925, -6.7521, 11.7512, -0.0447, -0.0035, 0.0057, 0.9990, 59.2868, -36.1605, -0.6516, 0.0173, 0.0170, 0.7582, 67.6297, -39.6285, -0.6003, 0.0197, 0.0142, 0.7994 },
	{ -0.6254, 13.6937, -0.1147, -0.0006, 0.0061, 0.9934, -8.9786, 12.0662, -0.0279, -0.0011, 0.0060, 0.9996, 63.7464, -36.8724, -0.6758, 0.0181, 0.0162, 0.7367, 63.2051, -40.5941, -0.5019, 0.0202, 0.0135, 0.8646 },
	{ -3.1439, 15.2112, -0.1058, 0.0018, 0.0061, 0.9944, -11.0679, 12.1232, -0.0099, 0.0012, 0.0063, 0.9999, 67.5112, -36.8166, -0.6983, 0.0186, 0.0150, 0.7154, 54.9158, -39.3494, -0.3737, 0.0203, 0.0126, 0.9272 },
	{ -5.5364, 16.4629, -0.0956, 0.0042, 0.0061, 0.9954, -13.6968, 13.7735, -0.0085, 0.0035, 0.0065, 0.9999, 70.2530, -36.8185, -0.7063, 0.0187, 0.0136, 0.7075, 44.0914, -34.9261, -0.2404, 0.0202, 0.0113, 0.9704 },
	{ -7.8021, 17.4538, -0.0843, 0.0064, 0.0060, 0.9964, -19.5606, 25.6297, -0.1176, 0.0058, 0.0066, 0.9930, 71.7893, -37.6652, -0.6894, 0.0184, 0.0120, 0.7241, 33.2255, -27.7613, -0.1302, 0.0198, 0.0095, 0.9912 },
	{ -9.9389, 18.1862, -0.0718, 0.0086, 0.0058, 0.9974, -23.8732, 42.0050, -0.3314, 0.0080, 0.0066, 0.9434, 71.5308, -39.3500, -0.6404, 0.0177, 0.0102, 0.7678, 24.1419, -19.3719, -0.0562, 0.0191, 0.0073, 0.9982 },
	{ -11.9430, 18.6603, -0.0583, 0.0106, 0.0056, 0.9982, -20.9562, 51.7668, -0.5520, 0.0099, 0.0067, 0.8338, 68.3033, -40.9543, -0.5540, 0.0165, 0.0085, 0.8323, 18.1710, -12.5305, -0.0124, 0.0178, 0.0051, 0.9998 },
	{ -13.8098, 18.8744, -0.0437, 0.0124, 0.0053, 0.9990, -14.6316, 52.9243, -0.6882, 0.0116, 0.0069, 0.7254, 61.0911, -40.8989, -0.4324, 0.0148, 0.0068, 0.9015, 15.2456, -8.3707, 0.0088, 0.0160, 0.0034, 0.9998 },
	{ -15.7022, 19.3116, -0.0330, 0.0140, 0.0050, 0.9993, -12.5829, 52.5031, -0.7331, 0.0131, 0.0071, 0.6800, 50.4980, -37.8177, -0.2944, 0.0129, 0.0051, 0.9556, 14.1978, -5.8936, 0.0099, 0.0137, 0.0019, 0.9999 },
	{ -19.9192, 27.1826, -0.1045, 0.0155, 0.0045, 0.9944, -14.3368, 53.5935, -0.7323, 0.0146, 0.0069, 0.6808, 38.9332, -31.6268, -0.1707, 0.0108, 0.0031, 0.9853, 14.3573, -4.8359, 0.0006, 0.0112, 0.0008, 0.9999 },
	{ -24.2271, 42.1914, -0.2945, 0.0167, 0.0040, 0.9555, -14.1722, 54.3833, -0.7418, 0.0159, 0.0064, 0.6704, 28.7114, -23.5951, -0.0816, 0.0084, 0.0011, 0.9966, 15.4482, -4.9697, -0.0159, 0.0084, -0.0002, 0.9998 },
	{ -22.0386, 53.2806, -0.5228, 0.0175, 0.0036, 0.8523, -12.2987, 54.9959, -0.7699, 0.0169, 0.0058, 0.6379, 21.1508, -15.8758, -0.0279, 0.0056, -0.0006, 0.9996, 18.7353, -6.9615, -0.0564, 0.0055, -0.0011, 0.9984 },
	{ -14.6157, 55.1604, -0.6836, 0.0181, 0.0036, 0.7297, -8.1455, 54.5820, -0.8130, 0.0177, 0.0053, 0.5820, 17.2252, -11.2620, 0.0023, 0.0026, -0.0020, 1.0000, 22.0299, -8.9349, -0.0979, 0.0026, -0.0021, 0.9952 }
}

-- regard au repos : { instant, cap, hauteur }
local SACCADES = { { 0.06, 18, 4 }, { 0.2, 25, -3 }, { 0.34, -3, 1 }, { 0.45, -22, 5 }, { 0.58, -27, -4 }, { 0.72, -6, 7 }, { 0.84, 3, -1 } }

local function ease(a, b, t)
	local x = clamp((t - a) / (b - a), 0, 1)
	return x * x * (3 - 2 * x)
end

local function rot(v)
	return CFrame.fromEulerAnglesYXZ(rad(v[1]), rad(v[2]), rad(v[3]))
end

local function blink(t, at, d)
	return clamp(1 - abs(t - at) / (d or 0.06), 0, 1) ^ 0.7
end

-- interpolation Catmull-Rom périodique (comme course_v6.catmull)
local function catmull(tab, s)
	local n = #tab
	local x = (s % 1) * n
	local i = math.floor(x)
	local f = x - i
	local p0, p1, p2, p3 = tab[(i - 1) % n + 1], tab[i % n + 1], tab[(i + 1) % n + 1], tab[(i + 2) % n + 1]
	local out = table.create(#p1)
	for k = 1, #p1 do
		out[k] = 0.5 * (2 * p1[k] + (p2[k] - p0[k]) * f + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f * f
			+ (3 * p1[k] - p0[k] - 3 * p2[k] + p3[k]) * f * f * f)
	end
	return out
end

local function quat(x, y, z, w)
	local n = math.sqrt(x * x + y * y + z * z + w * w)
	return CFrame.new(0, 0, 0, x / n, y / n, z / n, w / n)
end

-- valeur k (2 = cap, 3 = hauteur) du regard au repos, transitions de durée dur
local function cible(t, k, dur, delai)
	delai = delai or 0
	local v = SACCADES[#SACCADES][k]
	for i, s in SACCADES do
		local prev = SACCADES[i == 1 and #SACCADES or i - 1]
		v += (s[k] - prev[k]) * ease(s[1] + delai, s[1] + delai + dur, t)
	end
	return v
end

local function sides(P, name, ex, ey, ez)
	P[name .. "R"] = { ex, ey, ez }
	P[name .. "L"] = { ex, -ey, -ez }
end

local function folded(P)
	sides(P, "WingUpper", 0, -38, -22)
	sides(P, "WingLower", 0, -68, 0)
	return P
end

local ANIMS = {}
ANIMS.Course = { duree = 2.2, fn = function(t)
	local s = (t * 2) % 1
	local ph = TAU * s
	local P = {}
	P.Root = { 2.0 * sin(ph - 0.4), 2.5 * sin(ph), 1.2 * sin(ph + 0.3) }
	P.Spine = { -3.0 * sin(ph + 0.3), -2.0 * sin(ph + 0.5), 0 }
	P.Chest = { 1.8 * sin(ph + 1.0), -1.5 * sin(ph + 0.9), -0.8 * sin(ph + 0.9) }
	P.Neck1 = { -7 + 2.5 * sin(ph + 1.6), 1.5 * sin(ph + 1.3), 0 }
	P.Neck2 = { -3 + 1.5 * sin(ph + 2.0), 1.0 * sin(ph + 1.7), 0 }
	P.Neck3 = { 1.0 * sin(ph + 2.4), 0, 0 }
	-- tête stabilisée : compense presque tout le tangage et le lacet du tronc et du cou
	local tang, lac = 0, 0
	for _, n in { "Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3" } do
		tang += P[n][1]
	end
	for _, n in { "Root", "Spine", "Chest", "Neck1", "Neck2" } do
		lac += P[n][2]
	end
	P.Head = { -0.85 * tang - 8 + 1.0 * sin(ph + 2.8), -0.7 * lac, -0.6 * (P.Root[3] + P.Chest[3]) }
	P.Jaw = { -6 - 4 * (0.5 + 0.5 * sin(ph + 2.2)), 0, 0 }
	sides(P, "WingUpper", 0, -38, -22 + 3 * sin(ph - 0.8))
	sides(P, "WingLower", 0, -68, 2 * sin(ph - 1.4))
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { -1.5 + 2.5 * sin(ph - 0.6 * i - 0.8) + 0.6 * sin(2 * ph - 0.9 * i),
			(3 + 1.2 * i) * sin(ph - 0.75 * i - 0.5), 0 }
	end
	local v = catmull(COURSE, s)
	local c = 0
	for _, kind in { "Front", "Back" } do
		for _, sd in { "R", "L" } do
			P[kind .. "UpperLeg" .. sd] = { v[c + 1], 0, 0 }
			P[kind .. "LowerLeg" .. sd] = { v[c + 2], 0, 0 }
			P[kind .. "Foot" .. sd] = quat(v[c + 3], v[c + 4], v[c + 5], v[c + 6])
			c += 6
		end
	end
	return P, Vector3.new(0, -0.32 + 0.1 * cos(ph - TAU * 0.78), 0.12 * sin(ph - 1.2)), 0.15
end }

ANIMS.Vol = { duree = 2.2, fn = function(t)
	local p = TAU * 2 * t
	local P = { Root = { -4 + 3 * sin(p + 0.6), 0, 0 }, Spine = { 2 * sin(p + 1.0), 0, 0 }, Chest = { 2 * sin(p + 1.4), 0, 0 },
		Neck1 = { -8 + 3 * sin(p + 1.4), 0, 0 }, Neck2 = { -4 + 2 * sin(p + 1.8), 0, 0 },
		Head = { 8 - 3 * sin(p + 2.2), 0, 0 }, Jaw = { -4, 0, 0 } }
	sides(P, "WingUpper", 0, 4 * cos(p), 38 * sin(p) + 8)
	sides(P, "WingLower", 0, 6 * cos(p), 30 * sin(p - 0.7) - 4)
	for j = 0, 3 do
		sides(P, "WingFinger" .. (j + 1), 0, 3 * j * cos(p - 1.2), 10 * sin(p - 1.3 - 0.2 * j))
	end
	sides(P, "FrontUpperLeg", -22, 0, 0)
	sides(P, "FrontLowerLeg", 48, 0, 0)
	sides(P, "FrontFoot", -35, 0, 0)
	sides(P, "BackUpperLeg", -28 + 3 * sin(p), 0, 0)
	sides(P, "BackLowerLeg", -12, 0, 0)
	sides(P, "BackFoot", -35, 0, 0)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 3 * sin(p - 0.8 * i) + (i == 0 and 3 or 0), 5 * sin(0.5 * p - 0.6 * i), 0 }
	end
	return P, Vector3.new(0, 4.5 - 0.7 * sin(p), 0), blink(t, 0.62), 0, 8 * sin(TAU * t)
end }

ANIMS.Rugissement = { duree = 2.2, boucle = false, fn = function(t)
	local a = ease(0, 0.22, t) * (1 - ease(0.3, 0.42, t))
	local r = ease(0.3, 0.42, t) * (1 - ease(0.82, 0.98, t))
	local sh = r * sin(TAU * t * 14)
	local P = { Root = { 6 * a - 3 * r, 0, 0 }, Spine = { 3 * a, 0, 0 }, Chest = { 3 * a - 2 * r, 0, 0 } }
	for i = 1, 3 do
		P["Neck" .. i] = { 7 * a - 4 * r, 0, 0 }
	end
	P.Head = { 12 * a + 8 * r + 2 * sh, 2 * sh, 0 }
	P.Jaw = { -6 * a - 34 * r, 0, 0 }
	local f = 1 - a - r
	sides(P, "WingUpper", 0, -38 * f - 10 * r, -22 * f + 25 * a + 45 * r)
	sides(P, "WingLower", 0, -68 * f + 8 * r, 10 * a + 25 * r)
	for j = 0, 3 do
		sides(P, "WingFinger" .. (j + 1), 0, (j - 1.5) * 6 * r, 4 * r * sin(TAU * t * 7 + j))
	end
	sides(P, "FrontUpperLeg", -14 * a + 10 * r, 0, 0)
	sides(P, "FrontLowerLeg", 10 * a - 8 * r, 0, 0)
	sides(P, "FrontFoot", 6 * a, 0, 0)
	sides(P, "BackUpperLeg", -6 * a - 6 * r, 0, 0)
	sides(P, "BackLowerLeg", 4 * a, 0, 0)
	sides(P, "BackFoot", 2 * a + 6 * r, 0, 0)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 4 * a + 3 * r, 12 * r * sin(TAU * t * 3 - 0.8 * i), 0 }
	end
	return P, Vector3.new(0, 0.45 * a - 0.15 * r, 0), 0.4 * r + blink(t, 0.12), r
end }

-- repos : l'œil saute vers un point (~50 ms), la tête suit plus lentement pendant que l'œil revient au centre
ANIMS.Repos = { duree = 4.0, fn = function(t)
	local br = sin(TAU * t)
	local tc, th = 0.65 * cible(t, 2, 0.1, 0.02), 0.5 * cible(t, 3, 0.1, 0.02)
	local cap = clamp(cible(t, 2, 0.012) - tc, -18, 18) + 0.7 * sin(19 * TAU * t) + 0.4 * sin(31 * TAU * t + 1)
	local haut = clamp(cible(t, 3, 0.012) - th, -9, 9) + 0.5 * sin(23 * TAU * t + 2)
	local lourd = 0.35 * ease(0.58, 0.62, t) * (1 - ease(0.70, 0.73, t))
	local lid = 0.08 + lourd - 0.02 * haut + max(blink(t, 0.45, 0.03), blink(t, 0.83, 0.03), blink(t, 0.89, 0.03))
	local P = folded({ Chest = { 1.5 * br, 0, 0 }, Spine = { -br, 0, 0 },
		Neck1 = { 2 * br, 0.3 * tc, 0 }, Neck2 = { br, 0.3 * tc, 0 }, Neck3 = { 0.4 * th, 0.2 * tc, 0 },
		Head = { -2 * br + 0.6 * th, 0.2 * tc, 0 }, Jaw = { -3 - 3 * max(0, br), 0, 0 } })
	sides(P, "WingUpper", 0, -38, -22 + 2 * br)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 1.5 * sin(TAU * t - 0.5 * i), 6 * sin(TAU * t - 0.6 * i), 0 }
	end
	return P, Vector3.new(0, 0.05 * br, 0), lid, 0, cap, haut
end }

function Anim.new(model: Model)
	local self = setmetatable({}, Anim)
	self.model = model
	self.bones = {}
	for _, b in model:GetDescendants() do
		if b:IsA("Bone") then
			self.bones[b.Name] = b
		end
	end
	for _, n in BONES do
		assert(self.bones[n], "Os introuvable : " .. n)
	end
	self.neon = model:FindFirstChild("DragonNeon", true)
	if self.neon then
		self.neon.Material = Enum.Material.Neon
		self.baseColor = self.neon.Color
	end
	self.current, self.t = "Repos", 0
	self.blinkT, self.squintV, self.lookV, self.lookUpV, self.rate = math.huge, 0, nil, nil, 1
	self.conn = RunService.Heartbeat:Connect(function(dt)
		self:step(dt)
	end)
	return self
end

function Anim:play(name: string)
	assert(ANIMS[name], "Animation inconnue : " .. tostring(name))
	self.current, self.t = name, 0
end

function Anim:blink()
	self.blinkT = 0
end

function Anim:look(deg: number?, up: number?)
	self.lookV, self.lookUpV = deg, up -- nil : le regard suit l'animation
end

function Anim:setRate(r: number)
	self.rate = max(r, 0) -- vitesse de lecture (1 = normale)
end

function Anim:squint(v: number)
	self.squintV = clamp(v, 0, 1)
end

function Anim:step(dt)
	local A = ANIMS[self.current]
	self.t += dt * self.rate / A.duree
	if self.t >= 1 then
		if A.boucle == false then
			self.current, self.t = "Repos", 0
			A = ANIMS.Repos
		else
			self.t %= 1
		end
	end
	local P, off, squint, roar, look, lookUp = A.fn(self.t)
	-- clignement : à la demande + un au hasard toutes les 3 à 6 s
	self.blinkT += dt
	if self.blinkT > 0.25 and math.random() < dt / 4.5 then
		self.blinkT = 0
	end
	local bl = clamp(1 - abs(self.blinkT - 0.08) / 0.08, 0, 1)
	local lid = clamp(max(bl, squint or 0, self.squintV), 0, 1)
	look = self.lookV or look or 0
	lookUp = self.lookUpV or lookUp or 0
	for _, s in { "R", "L" } do
		P["Eyelid" .. s] = CFrame.fromAxisAngle(LID_AXIS[s], -LID_CLOSE * lid * (s == "R" and 1 or -1))
		P["Pupil" .. s] = CFrame.fromEulerAnglesYXZ(0, rad(-look), 0) * CFrame.fromAxisAngle(PUPIL_AXIS[s], rad(lookUp))
	end
	for _, n in BONES do
		local v = P[n]
		local cf = typeof(v) == "CFrame" and v or (v and rot(v) or CFrame.identity)
		if n == "Root" then
			cf = CFrame.new(off) * cf
		end
		self.bones[n].Transform = cf
	end
	-- lueur des yeux : pulsation lente, plus vive pendant le rugissement
	if self.neon then
		local k = 0.85 + 0.15 * sin(os.clock() * 2.5) + 0.3 * (roar or 0)
		self.neon.Color = Color3.new(math.min(self.baseColor.R * k, 1), math.min(self.baseColor.G * k, 1),
			math.min(self.baseColor.B * k, 1))
	end
end

function Anim:destroy()
	self.conn:Disconnect()
end

return Anim
