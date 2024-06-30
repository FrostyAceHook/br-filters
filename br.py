import numpy as np
from pymclevel import TileEntity, Entity


# Selector string syntax.
#   Used to produce a boolean array of the blocks in a selection, effectively
#   selecting the blocks that =true.
#
#
# Form: empty :DD
# selector =
# - Selector is nothing (or just whitespace).
# - The entire selection matches.
#
#
# Form: simple :D
# selector = ["!"] id [":" data]
# - "!" inverts the selection.
# - `id` is the block id (may be a word which is looked-up to an integer).
# - `data` is the block data (may be a word which is looked-up to an integer).
# - If no `data` is given, any data type matches.
#
#
# Form: complex >:(
# ==================
# selector = top_expr
# - `top_expr` must be an `expr` of type bool.
# - Only parsed if the selector is invalid under simple form.
#
# `expr`:
#   _____________________________________________________________
#  |_expression_format_|__type___|__________explanation__________|
#  |_"id"______________|_integer_|_the_current_block's_id________|
#  |_"i"_______________|_integer_|_the_current_block's_id________|
#  |_"data"____________|_integer_|_the_current_block's_data______|
#  |_"d"_______________|_integer_|_the_current_block's_data______|
#  |_"("_expr_")"______|_expr____|_equal_to_expr_________________|
#  |_literal___________|_integer_|_an_integer____________________|
#  |_word______________|_integer_|_mapped_from_word_to_integer___|
#  |_expr_op_expr______|_bool____|_invokes_the_binary_operator___|
#  |_op_expr___________|_bool____|_invokes_the_unary_operator____|
#
# `op`: (a and b are both `expr` of the same type), listed in precedence order.
#       Note that associativity is irrelevant since all these are associative, or
#       the argument would be of the wrong type.
#   _____________________________________________________________________
#  |_operator_format_|_class__|_type_of_a_|_________explanation__________|
#  |_!a______________|_prefix_|_bool______|_not_a________________________|
#  |_a=b_____________|_binary_|_integer___|_a_equal_to_b_________________|
#  |_a==b____________|_binary_|_integer___|_a_equal_to_b_________________|
#  |_a!=b____________|_binary_|_integer___|_a_not_equal_to_b_____________|
#  |_a<b_____________|_binary_|_integer___|_a_less_than_b________________|
#  |_a<=b____________|_binary_|_integer___|_a_less_than_or_equal_to_b____|
#  |_a>b_____________|_binary_|_integer___|_a_greater_than_b_____________|
#  |_a>=b____________|_binary_|_integer___|_a_greater_than_or_equal_to_b_|
#  |_a&b_____________|_binary_|_bool______|_a_and_b______________________|
#  |_a&&b____________|_binary_|_bool______|_a_and_b______________________|
#  |_a|b_____________|_binary_|_bool______|_a_or_b_______________________|
#  |_a||b____________|_binary_|_bool______|_a_or_b_______________________|
#
def selector(name, spec):

    def throw(desc):
        raise Exception("'{}' selector string: {}".format(name, desc))

    # Map of words to the ints they correspond to.
    LOOKUP = {
        # Colours.
        "white":        0,
        "orange":       1,
        "magenta":      2,
        "light_blue":   3,
        "yellow":       4,
        "lime":         5,
        "pink":         6,
        "grey":         7,
        "gray":         7, # inclusivity.
        "light_grey":   8,
        "light_gray":   8,
        "cyan":         9,
        "aqua":         9,
        "purple":       10,
        "blue":         11,
        "brown":        12,
        "green":        13,
        "greer":        13,
        "red":          14,
        "black":        15,


        # Blocks. Lots of alt spellings included for permissivity.
        "air":                              0,
        "ari":                              0,
        "stone":                            1,
        "sonte":                            1,
        "grass":                            2,
        "grass_block":                      2,
        "dirt":                             3,
        "cobble":                           4,
        "cobblestone":                      4,
        "planks":                           5,
        "wood_planks":                      5,
        "wooden_planks":                    5,
        "sapling":                          6,
        "bedrock":                          7,
        "flowing_water":                    8,
        "water":                            9,
        "flowing_lava":                     10,
        "lava":                             11,
        "sand":                             12,
        "gravel":                           13,
        "gold_ore":                         14,
        "iron_ore":                         15,
        "coal_ore":                         16,
        "log":                              17,
        "leaf":                             18,
        "leaves":                           18,
        "sponge":                           19,
        "glass":                            20,
        "lapis_ore":                        21,
        "lapis_lazuli_ore":                 21,
        "lapis":                            22,
        "lapis_block":                      22,
        "lapis_lazuli_block":               22,
        "dispenser":                        23,
        "sandstone":                        24,
        "noteblock":                        25,
        "bed":                              26,
        "golden_rail":                      27,
        "powered_rail":                     27,
        "detector_rail":                    28,
        "sticky_piston":                    29,
        "web":                              30,
        "tallgrass":                        31,
        "deadbush":                         32,
        "piston":                           33,
        "piston_head":                      34,
        "wool":                             35,
        "piston_extension":                 36,
        "yellow_flower":                    37,
        "red_flower":                       38,
        "brown_mushroom":                   39,
        "red_mushroom":                     40,
        "gold":                             41,
        "gold_block":                       41,
        "iron":                             42,
        "iron_block":                       42,
        "double_stone_slab":                43,
        "stone_slab":                       44,
        "brick":                            45,
        "bricks":                           45,
        "brick_block":                      45,
        "tnt":                              46,
        "bookshelf":                        47,
        "mossy_cobble":                     48,
        "mossy_cobblestone":                48,
        "obsidian":                         49,
        "torch":                            50,
        "fire":                             51,
        "spawner":                          52,
        "mob_spawner":                      52,
        "monster_spawner":                  52,
        "oak_stair":                        53,
        "oak_stairs":                       53,
        "chest":                            54,
        "redstone_wire":                    55,
        "diamond_ore":                      56,
        "diamond":                          57,
        "diamond_block":                    57,
        "crafting_table":                   58,
        "wheat":                            59,
        "farm":                             60,
        "farmland":                         60,
        "tilled_dirt":                      60,
        "furnace":                          61,
        "lit_furnace":                      62,
        "standing_sign":                    63,
        "wooden_door":                      64,
        "ladder":                           65,
        "rail":                             66,
        "stone_stair":                      67,
        "stone_stairs":                     67,
        "wall_sign":                        68,
        "lever":                            69,
        "stone_pressure_plate":             70,
        "iron_door":                        71,
        "wooden_pressure_plate":            72,
        "redstone_ore":                     73,
        "lit_redstone_ore":                 74,
        "unlit_redstone_torch":             75,
        "redstone_torch":                   76,
        "lit_redstone_torch":               76,
        "stone_button":                     77,
        "snow_layer":                       78,
        "ice":                              79,
        "snow":                             80,
        "snow_block":                       80,
        "cactus":                           81,
        "clay":                             82,
        "reed":                             83,
        "reeds":                            83,
        "sugar_cane":                       83,
        "jukebox":                          84,
        "fence":                            85,
        "pumpkin":                          86,
        "pumpkin_block":                    86,
        "netherrack":                       87,
        "soulsand":                         88,
        "soul_sand":                        88,
        "glowstone":                        89,
        "portal":                           90,
        "lit_pumpkin":                      91,
        "cake":                             92,
        "unpowered_repeater":               93,
        "powered_repeater":                 94,
        "stained_glass":                    95,
        "trapdoor":                         96,
        "monster_egg":                      97,
        "stonebrick":                       98,
        "stonebricks":                      98,
        "brown_mushroom_block":             99,
        "red_mushroom_block":               100,
        "iron_bar":                         101,
        "iron_bars":                        101,
        "pane":                             102,
        "panes":                            102,
        "glass_pane":                       102,
        "glass_panes":                      102,
        "melon":                            103,
        "melon_block":                      103,
        "pumpkin_stem":                     104,
        "melon_stem":                       105,
        "vine":                             106,
        "vines":                            106,
        "fence_gate":                       107,
        "brick_stair":                      108,
        "brick_stairs":                     108,
        "stone_brick_stair":                109,
        "stone_brick_stairs":               109,
        "mycelium":                         110,
        "lilypad":                          111,
        "lily_pad":                         111,
        "waterlily":                        111,
        "water_lily":                       111,
        "nether_brick":                     112,
        "nether_brick_fence":               113,
        "nether_brick_stair":               114,
        "nether_brick_stairs":              114,
        "netherwart":                       115,
        "netherwarts":                      115,
        "nether_wart":                      115,
        "nether_warts":                     115,
        "enchant_table":                    116,
        "enchanting_table":                 116,
        "enchantment_table":                116,
        "brewing_stand":                    117,
        "cauldron":                         118,
        "end_portal":                       119,
        "ender_portal":                     119,
        "end_portal_frame":                 120,
        "ender_portal_frame":               120,
        "end_stone":                        121,
        "dragon_egg":                       122,
        "ender_dragon_egg":                 122,
        "redstone_lamp":                    123,
        "lit_redstone_lamp":                124,
        "litty_redstone_lamp":              124,
        "double_wooden_slab":               125,
        "wooden_slab":                      126,
        "cocoa":                            127,
        "sandstone_stair":                  128,
        "sandstone_stairs":                 128,
        "emerald_ore":                      129,
        "ender_chest":                      130,
        "tripwire_hook":                    131,
        "tripwire_hoog":                    131,
        "tripwire":                         132,
        "emerald_block":                    133,
        "spruce_stair":                     134,
        "spruce_stairs":                    134,
        "birch_stair":                      135,
        "birch_stairs":                     135,
        "jungle_stair":                     136,
        "jungle_stairs":                    136,
        "command_block":                    137,
        "beacon":                           138,
        "cobblestone_wall":                 139,
        "pot":                              140,
        "flower_pot":                       140,
        "carrot":                           141,
        "carrots":                          141,
        "potato":                           142,
        "potatos":                          142,
        "potatoes":                         142,
        "wooden_button":                    143,
        "head":                             144,
        "skull":                            144,
        "skull_emoji":                      144,
        "anvil":                            145,
        "trapped_chest":                    146,
        "gold_pressure_plate":              147,
        "light_weighted_pressure_plate":    147,
        "iron_pressure_plate":              148, # but gold is denser...
        "heavy_weighted_pressure_plate":    148,
        "unpowered_comparator":             149,
        "powered_comparator":               150,
        "daylight_sensor":                  151,
        "daylight_detector":                151,
        "redstone_block":                   152,
        "quartz_ore":                       153,
        "hopper":                           154,
        "quartz":                           155,
        "quartz_block":                     155,
        "quartz_stair":                     156,
        "quartz_stairs":                    156,
        "activator_rail":                   157,
        "dropper":                          158,
        "stained_terracotta":               159,
        "stained_hardened_clay":            159,
        "stained_pane":                     160,
        "stained_panes":                    160,
        "stained_glass_pane":               160,
        "stained_glass_panes":              160,
        "leaves2":                          161,
        "log2":                             162,
        "acacia_stair":                     163,
        "acacia_stairs":                    163,
        "dark_oak_stair":                   164,
        "dark_oak_stairs":                  164,
        "slime":                            165,
        "slime_block":                      165,
        "barrier":                          166,
        "barrier_block":                    166,
        "iron_trapdoor":                    167,
        "prismarine":                       168,
        "sea_lantern":                      169,
        "hay":                              170,
        "hay_bale":                         170,
        "hay_block":                        170,
        "carpet":                           171,
        "terracotta":                       172,
        "hardened_clay":                    172,
        "coal":                             173,
        "coal_block":                       173,
        "packed_ice":                       174,
        "double_plant":                     175,
        "standing_banner":                  176,
        "wall_banner":                      177,
        "daylight_detector_inverted":       178,
        "red_sandstone":                    179,
        "red_sandstone_stair":              180,
        "red_sandstone_stairs":             180,
        "double_stone_slab2":               181,
        "stone_slab2":                      182,
        "spruce_fence_gate":                183,
        "birch_fence_gate":                 184,
        "jungle_fence_gate":                185,
        "dark_oak_fence_gate":              186,
        "acacia_fence_gate":                187,
        "spruce_fence":                     188,
        "birch_fence":                      189,
        "jungle_fence":                     190,
        "dark_oak_fence":                   191,
        "acacia_fence":                     192,
        "spruce_door":                      193,
        "birch_door":                       194,
        "jungle_door":                      195,
        "acacia_door":                      196,
        "dark_oak_door":                    197,
        "end_rod":                          198,
        "chorus_plant":                     199,
        "chorus_flower":                    200,
        "purpur_block":                     201,
        "purpur_pillar":                    202,
        "purpur_stair":                     203,
        "purpur_stairs":                    203,
        "purpur_double_slab":               204,
        "purpur_slab":                      205,
        "end_brick":                        206,
        "end_bricks":                       206,
        "beetroot":                         207,
        "beetroots":                        207,
        "path":                             208,
        "grass_path":                       208,
        "end_gateway":                      209,
        "repeating_command_block":          210,
        "chain_command_block":              211,
        "frosted_ice":                      212,
        "magma":                            213,
        "magma_block":                      213,
        "netherwart_block":                 214,
        "nether_wart_block":                214,
        "red_nether_brick":                 215,
        "bone":                             216,
        "bone_block":                       216,
        "structure_void":                   217,
        "observer":                         218,
        "white_shulker":                    219,
        "white_shulker_box":                219,
        "orange_shulker":                   220,
        "orange_shulker_box":               220,
        "magenta_shulker":                  221,
        "magenta_shulker_box":              221,
        "light_blue_shulker":               222,
        "light_blue_shulker_box":           222,
        "yellow_shulker":                   223,
        "yellow_shulker_box":               223,
        "lime_shulker":                     224,
        "lime_shulker_box":                 224,
        "pink_shulker":                     225,
        "pink_shulker_box":                 225,
        "grey_shulker":                     226,
        "gray_shulker":                     226,
        "grey_shulker_box":                 226,
        "gray_shulker_box":                 226,
        "light_grey_shulker":               227,
        "light_gray_shulker":               227,
        "light_grey_shulker_box":           227,
        "light_gray_shulker_box":           227,
        "cyan_shulker":                     228,
        "cyan_shulker_box":                 228,
        "purple_shulker":                   229,
        "purple_shulker_box":               229,
        "blue_shulker":                     230,
        "blue_shulker_box":                 230,
        "brown_shulker":                    231,
        "brown_shulker_box":                231,
        "green_shulker":                    232,
        "green_shulker_box":                232,
        "red_shulker":                      233,
        "red_shulker_box":                  233,
        "black_shulker":                    234,
        "black_shulker_box":                234,
        "white_glazed_terracotta":          235,
        "orange_glazed_terracotta":         236,
        "magenta_glazed_terracotta":        237,
        "light_blue_glazed_terracotta":     238,
        "yellow_glazed_terracotta":         239,
        "lime_glazed_terracotta":           240,
        "pink_glazed_terracotta":           241,
        "grey_glazed_terracotta":           242,
        "gray_glazed_terracotta":           242,
        "light_grey_glazed_terracotta":     243,
        "light_gray_glazed_terracotta":     243,
        "cyan_glazed_terracotta":           244,
        "purple_glazed_terracotta":         245,
        "blue_glazed_terracotta":           246,
        "brown_glazed_terracotta":          247,
        "green_glazed_terracotta":          248,
        "red_glazed_terracotta":            249,
        "black_glazed_terracotta":          250,
        "concrete":                         251,
        "concrete_powder":                  252,
        "structure_block":                  255,
    }


    class Empty:
        def __init__(self):
            pass

        def is_integer(self):
            # nog
            return False

        def do(self, ids, datas):
            return np.ones(ids.shape, dtype=bool)

        def __repr__(self):
            return "matches all"


    class Simple:
        def __init__(self):
            self.bid = None
            self.bdata = None
            self.is_except = False

        def is_integer(self):
            # is not
            return False

        def do(self, ids, datas):
            assert self.bid is not None
            if not self.is_except:
                mask = (ids == self.bid)
                if self.bdata is not None:
                    mask &= (datas == self.bdata)
            else:
                mask = (ids != self.bid)
                if self.bdata is not None:
                    mask |= (datas != self.bdata)
            return mask

        def __repr__(self):
            assert self.bid is not None
            bid = self.bid
            bdata = "any" if self.bdata is None else self.bdata
            prefix = "not " if self.is_except else ""
            return "{}{}:{}".format(prefix, bid, bdata)



    # Node ids. Set to strings instead of enum for convenience/printing.

    OPEN    = "("
    CLOSE   = ")"
    COLON   = ":"

    ID      = "id"
    DATA    = "data"
    INT     = "int"

    NOT     = "!"

    EQ      = "="
    NEQ     = "!="
    LT      = "<"
    LTE     = "<="
    GT      = ">"
    GTE     = ">="
    AND     = "&"
    OR      = "|"

    # Operators listed in ascending precedence.
    PRECEDENCE = (OR, AND, GTE, GT, LTE, LT, NEQ, EQ, NOT)


    class Token:
        TYPES = {
            OPEN:   type(None),
            CLOSE:  type(None),
            COLON:  type(None),

            ID:     type(None),
            DATA:   type(None),
            INT:    int,

            NOT:    type(None),

            EQ:     type(None),
            NEQ:    type(None),
            LT:     type(None),
            LTE:    type(None),
            GT:     type(None),
            GTE:    type(None),
            AND:    type(None),
            OR:     type(None),
        }

        def __init__(self, t, v=None):
            assert t in self.TYPES and self.TYPES[t] == type(v)
            self.t = t
            self.v = v

        def __repr__(self):
            if self.t == INT:
                return str(self.v)
            else:
                return self.t


    def peek(s, n=1):
        return s[0:n].lower()

    def adv(s, n=1):
        assert len(s) >= n
        return s[n:]

    def token(s):
        if not s:
            return s, None
        c = peek(s)

        # Ignore whitespace.
        if c.isspace():
            return adv(s), None

        # Parse integer literals.
        dig = "0123456789"
        if c in dig:
            v = 0
            while peek(s) and peek(s) in dig:
                v = 10*v + dig.index(peek(s))
                s = adv(s)
            return s, Token(INT, v)

        # Parse words (including id and data tokens).
        abc = "abcdefghijklmnopqrstuvwxyz_"
        abcnum = abc + "0123456789"
        if c in abc: # cant start with a digit.
            w = ""
            while peek(s) and peek(s) in abcnum: # may have digits in the rest.
                w += peek(s)
                s = adv(s)
            # Parse "id" (or shorthand).
            if w == "id" or w == "i":
                return s, Token(ID)
            # Parse "data" (or shorthand).
            if w == "data" or w == "d":
                return s, Token(DATA)
            # Parse other words.
            if w not in LOOKUP:
                throw("unrecognised word \"{}\"".format(w))
            return s, Token(INT, LOOKUP[w])

        # Check fixed patterns last.
        fixed = (
            ("(",   OPEN),
            (")",   CLOSE),
            (":",   COLON),
            ("!",   NOT),
            ("=",   EQ),
            ("==",  EQ),
            ("!=",  NEQ),
            ("<",   LT),
            ("<=",  LTE),
            (">",   GT),
            (">=",  GTE),
            ("&",   AND),
            ("&&",  AND),
            ("|",   OR),
            ("||",  OR),
        )
        # From largest to smallest to do greedy tokenising (otherwise != would
        # be tokenised as NOT, EQ)
        fixed = sorted(fixed, reverse=True, key=lambda x: len(x[0]))
        for pattern, t in fixed:
            if pattern == peek(s, len(pattern)):
                return adv(s, len(pattern)), Token(t)

        throw("illegal character \"{}\"".format(c))




    # Always an expr of type integer.
    # One of:
    # - an integer
    # - the id array
    # - the data array
    class Value:
        TYPES = {
            ID:     type(None),
            DATA:   type(None),
            INT:    int,
        }
        def __init__(self, t, v=None):
            assert t in self.TYPES and self.TYPES[t] == type(v)
            self.t = t
            self.v = v

        def is_integer(self):
            # all current values are integers.
            return True

        def do(self, ids, datas):
            if self.t == INT:
                return self.v
            if self.t == ID:
                return ids
            if self.t == DATA:
                return datas
            assert False

        def __repr__(self):
            if self.t == INT:
                return str(self.v)
            if self.t == ID:
                return "id"
            if self.t == DATA:
                return "data"
            assert False

    class PrefixOp:
        OPS = {
            NOT:    (0, np.logical_not),
        }
        def __init__(self, op, a):
            assert op in self.OPS
            if a.is_integer() != self.OPS[op][0]:
                throw("operator \"{}\" expected a".format(op) +
                        ("n integer" if self.OPS[op][0] else " bool") +
                        " argument")
            self.op = op
            self.a = a

        def is_integer(self):
            # all current operators return bool.
            return False

        def do(self, ids, datas):
            av = self.a.do(ids, datas)
            return self.OPS[self.op][1](av)

        def __repr__(self):
            return "({}{})".format(self.op, self.a)

    class BinaryOp:
        OPS = {
            EQ:     (1, lambda a,b: a == b),
            NEQ:    (1, lambda a,b: a != b),
            LT:     (1, lambda a,b: a < b),
            LTE:    (1, lambda a,b: a <= b),
            GT:     (1, lambda a,b: a > b),
            GTE:    (1, lambda a,b: a >= b),
            AND:    (0, np.logical_and),
            OR:     (0, np.logical_or),
        }
        def __init__(self, op, a, b):
            assert op in self.OPS
            if (a.is_integer() != self.OPS[op][0] or
                    b.is_integer() != self.OPS[op][0]):
                throw("operator \"{}\" expected".format(op) +
                        (" integer" if self.OPS[op][0] else " bool") +
                        " arguments.")
            self.op = op
            self.a = a
            self.b = b

        def is_integer(self):
            # all current operators return bool.
            return False

        def do(self, ids, datas):
            av = self.a.do(ids, datas)
            bv = self.b.do(ids, datas)
            return self.OPS[self.op][1](av, bv)

        def __repr__(self):
            return "({} {} {})".format(self.a, self.op, self.b)


    def parse_node(tokens):
        # `tokens` is a list of tokens or (previously evaluated) nodes.

        if not tokens:
            return None

        # To not echo deletions up the chain. annoying python.
        tokens = tokens[:]

        # Firstly, indentify the start,end indices of any top-level brackets.
        brackets = []
        depth = 0
        for i, token in enumerate(tokens):
            if not isinstance(token, Token):
                continue

            if token.t == OPEN:
                depth += 1
                if depth == 1:
                    brackets.append(i)
            elif token.t == CLOSE:
                depth -= 1
                if depth < 0:
                    throw("unexpected close bracket")
                if depth == 0:
                    # Check for an empty bracket here for a clearer error.
                    if i == brackets[-1] + 1:
                        throw("empty brackets")
                    brackets[-1] = [brackets[-1], i]

        if brackets and isinstance(brackets[-1], int):
            throw("unclosed bracket")


        # Evaluate the brackets.
        for i, pair in enumerate(brackets):
            inner = tokens[pair[0] + 1:pair[1]]
            node = parse_node(inner)

            # Replace the tokens with the node.
            del tokens[pair[0]:pair[1] + 1]
            tokens.insert(pair[0], node)

            # Adjust all the remaining bracket indices.
            dif = pair[1] - pair[0]
            for j in range(i + 1, len(brackets)):
                brackets[j][0] -= dif
                brackets[j][1] -= dif


        # If any operators are in the tokens, find the lowest precedence one and
        # evaluate it recursively. This becomes the value of the entire
        # expression.

        for op in PRECEDENCE:
            for i, token in enumerate(tokens):
                # Skip already-evaluated nodes.
                if not isinstance(token, Token):
                    continue

                if token.t != op:
                    continue

                # Check prefix operator.
                if token.t in PrefixOp.OPS:
                    a = parse_node(tokens[i + 1:])
                    if a is None:
                        throw("prefix operator \"{}\" ".format(op) +
                                "requires an argument")

                    # Constructor checks argument type.
                    return PrefixOp(op, a)

                # If it's a binary operator, evaluate each side.
                elif token.t in BinaryOp.OPS:
                    a = parse_node(tokens[:i])
                    b = parse_node(tokens[i + 1:])
                    if a is None:
                        throw("binary operator \"{}\" ".format(op) +
                                "requires a left argument")
                    if b is None:
                        throw("binary operator \"{}\" ".format(op) +
                                "requires a right argument")

                    # Constructor checks argument type.
                    return BinaryOp(op, a, b)


        # Otherwise the token list consists of nodes or values.

        if len(tokens) > 1:
            throw("must join adjacent expressions with an operator")
        token = tokens[0]

        # If it's a token, it must be a value.
        if isinstance(token, Token):
            # Catch tokens that aren't recognised in the complex syntax form.
            if token.t not in Value.TYPES:
                throw("the token \"{}\" cannot be used in ".format(token.t) +
                        "complex syntax")

            # The Token and Value valid states line up (definitely intentional
            # and not a nice coincidence).
            return Value(token.t, token.v)

        # Otherwise it's already an evaluated node.
        return token



    def parse(tokens):
        # Check empty form.
        if not tokens:
            return Empty()

        # Check if they are using simple form.
        try:
            # Simple syntax is: "[!]int[:int]"
            tks = tokens[:]
            simple = Simple()

            # Parse "[!]"
            if tks and tks[0].t == NOT:
                simple.is_except = True
                tks = adv(tks)

            # Parse "int"
            assert tks and tks[0].t == INT
            simple.bid = tks[0].v
            tks = adv(tks)

            # Parse "[:int]"
            if tks and tks[0].t == COLON:
                tks = adv(tks)
                assert tks and tks[0].t == INT
                simple.bdata = tks[0].v

            # Simple :D
            return simple

        except Exception: # this catches AssertionError or whatever.
            pass

        # Otherwise they using complex form >:(
        return parse_node(tokens)


    # Tokenise.
    tokens = []
    while spec:
        spec, t = token(spec)
        if t is not None:
            tokens.append(t)

    # Parse.
    top = parse(tokens)
    if top.is_integer():
        throw("must ultimately evaluate to a bool")

    # Objectify.
    sel = Sel(top)

    # Print it.
    print "'{}' selector: {}".format(name, sel)

    return sel


class Sel:
    def __init__(self, expr):
        self._top = expr

    def matches(self, ids, datas):
        return self._top.do(ids, datas)

    def __repr__(self):
        return repr(self._top)





BLOCKS = 0 # Iterate through the blocks.
SLICES = 1 # Iterate through the blocks and slices of the selection.
CHUNKS = 2 # Iterate through the chunks.
TES = 3 # Iterate through the tile entities.
ENTITIES = 4 # Iterate through the entities.

# Iterates through the selection of the level. The `method` argument determines
# the format of the yielded values. The yielded values are as follows:
# - BLOCKS: `ids` and `datas` in the selection, in x,z,y order.
# - SLICES: `ids` and `datas`, as well as a `slices` mask which represents the
#           current section of the overall selection, all in x,z,y order.
# - CHUNKS: every `chunk` in selection.
# - TES: every tile entity in selection, as the tile entity id (`eid`), position
#        in x,y,z order (`pos`), and the compound itself (`te`).
# - ENTITIES: every entity in selection, as the entity id (`eid`), position in
#        x,y,z order (`pos`), and the compound itself (`entity`).
def iterate(level, box, method, holey=False):
    # fucking finally found the culprit of the chunk skipping bug. i believe the
    # chunks were being unloaded before the changes could be made/saved/
    # something. idk exactly why this was happening, but keeping a reference in
    # here of every chunk seems to have fixed it.... so should be good....
    chunks = []

    # NEVERMIND IT STILL HAPPENS.
    # ok how about dirty every chunk immediately, AND keep a reference... surely
    # they cant get unloaded then?? or maybe that isn't even the culprit... it
    # does happen waaay less though now (after the previous change, haven't
    # tested this one yet, but that seems to indicate that the problem is at
    # least related to unloading).
    for chunk, slices, point in level.getChunkSlices(box):
        chunk.dirty = True
        chunks.append(chunk)


    # The `getChunkSlices` method will silently skip any chunks that don't exist,
    # but a lot of filters rely on the entire selection existing and being
    # iterated since blocks can influence other blocks. So we need to check that
    # the chunks do actually all exist. This isn't needed for all filters tho,
    # filters which only process entities have no need and filters explicitly
    # marked "holey" will be fine with missing chunks.
    if not (method in {TES, ENTITIES} or holey):
        for cx, cz in box.chunkPositions:
            if not level.containsChunk(cx, cz):
                raise Exception("Selection cannot contain missing chunks.")


    # Iterate through the level selection.
    for chunk, slices, point in level.getChunkSlices(box):
        # If the method is chunks, just yield the chunk.
        if method == CHUNKS:
            yield chunk
            continue

        # Entities and tile entites have a very similar api.
        if method == TES or method == ENTITIES:
            # Get the correct list of entities and their class.
            entities = chunk.TileEntities if (method == TES) else chunk.Entities
            entity_class = TileEntity if (method == TES) else Entity

            for entity in entities:
                # TileEntity and Entity have a position class method.
                pos = tuple(entity_class.pos(entity))

                # Still gotta bounds check.
                if pos not in box:
                    continue
                eid = entity["id"].value
                yield eid, pos, entity
            continue


        # The other methods all return the ids and datas.
        ids = chunk.Blocks[slices]
        datas = chunk.Data[slices]

        if method == BLOCKS:
            yield ids, datas
            continue

        # Get the properties of the current slice.
        pos = [point[i] for i in (0,2,1)]
        size = [s.stop - s.start for s in slices]

        # Make into slices for the overall selection.
        sel_slices = tuple(slice(p, p + s) for p, s in zip(pos, size))
        yield ids, datas, sel_slices
        continue




AXIS_X = 0 # Typically x-axis.
AXIS_Z = 1 # Typically z-axis.
AXIS_Y = 2 # Typically y-axis.
AXES = (AXIS_X, AXIS_Z, AXIS_Y) # All typical axes.

# Shifts the values of an array along an axis. Fills any now-empty values with 0
# if not clamping, otherwise fills it with the first perpendicular slice of the
# array along the shifted axis. `out` allows preallocated memory to be used,
# which must be the same shape and dtype as `array`. `out` may be the same
# memory as `array`, which causes an inplace shift.
def shift(array, by, axis, clamp=False, out=None):
    # No need - butch "Butch" Butch.
    if by == 0:
        if out is None:
            return np.copy(array)
        # Inplace shift of 0 is just nothing init.
        if out is array:
            return array

        # Otherwise use the memory provided.
        out[:] = array
        return out

    axis_len = array.shape[axis]

    # Create the array, if needed, which will be filled with the shifted `array`.
    if out is None:
        out = np.empty_like(array)


    # Slices the offset section of the shifted array to copy data to.
    shifted = slices(axis, abs(by), None)

    # Slices the section of the array to copy.
    unshifted = slices(axis, None, axis_len - abs(by))

    # If it's shifting backwards, just swap the slices.
    if by < 0:
        shifted, unshifted = unshifted, shifted


    # Do the shifted copy.
    out[shifted] = array[unshifted]


    # Now deal with the empty data.


    # Slices the empty part of the shifted array.
    empty = slices(axis, *((None, by) if (by > 0) else (by, None)))

    # If it's clamped gotta copy the data into the now empties.
    if clamp:
        # Slices the first non-empty slice of the shifted array, which is the
        # first slice of the original array. Do it like this so that `mem` can
        # actually be the same memory as array, if the original array is no
        # longer needed.
        clamped = slices(axis, *((by, by + 1) if (by > 0) else (by - 1, by)))

        # Fill the empty part.
        out[empty] = out[clamped]

    # Otherwise just zero fill.
    else:
        out[empty] = 0

    return out


# Same as `shift` however instead of only shifting along a single axis, shifts
# along all three axes by their respective `<axis>_by` slots.
def shift_xyz(array, x_by, y_by, z_by, clamp=False, out=None):
    if out is None and (x_by or y_by or z_by):
        out = np.copy(array)

    shift(array, x_by, AXIS_X, clamp=clamp, out=out)
    shift(out, y_by, AXIS_Y, clamp=clamp, out=out)
    shift(out, z_by, AXIS_Z, clamp=clamp, out=out)
    return out



# Returns the slices that would index `slice(start, end, step)` along the given
# axis, and then every element along the others.
def slices(axis, start, end, step=None):
    return axis*(slice(None),) + (slice(start, end, step),)


# Returns the shape of the box, in x,z,y order.
def shape(box):
    # Cheeky unpack, reorder and repack.
    w, h, l = box.size
    return w, l, h


# Returns the slices of the box, in x,z,y order.
def box_slices(box):
    x, y, z = [slice(p1, p2) for p1, p2 in zip(box.origin, box.maximum)]
    return x, z, y
