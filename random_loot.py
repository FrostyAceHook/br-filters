import br
import os
import random as rdm
from pymclevel import TAG_Byte, TAG_Short, TAG_Int, TAG_String, TAG_List, \
        TAG_Compound, TileEntity

displayName = "Random Loot"

inputs = (
    ("Fills chests with random loot based on some loot script. The loot script "
            "can consist of comments (lines beginning with \"#\"), which are "
            "ignored, and \"entries\", which add a possible item to the chest. "
            "An \"entry\" is a single line of the form:"
            "\n  percent_chance  item_id  item_data  amount"
            "\n  [ench1_id:ench1_lvl  ench1_id:ench2_lvl  ...]"
            "\nWhere:"
            "\n  percent_chance: number in 0..100; chance that"
            "\n    the item is added to a chest."
            "\n  item_id: string, without prefixing with"
            "\n    \"minecraft:\"; id of the item."
            "\n  item_data: integer in 0..32767; data value of"
            "\n    the item."
            "\n  amount: integer in 0..255; amount of the item in"
            "\n    this stack (yep, some versions can over-stack"
            "\n    and it can stack non-stackables)."
            "\n  ench_id: integer, valid enchant id; dictates one"
            "\n    enchantment of the item."
            "\n  ench_lvl: integer in 1..32767; dictates the"
            "\n    level of the paired enchantment id."
            "\nNote the enchantments are optional."
            , "label"),
    # Example entry:
    # 45.1 dirt 0 64 16:1 17:1
    # which has a 45.1% chance of adding a stack of dirt with sharpness 1 and
    # smite 1.

    ("Loot script path:", "string"),
    ("Note that \"/\" may be used to separate directories regardless of "
            "platform. If the path begins with \"./\", it is relative to the "
            "filter folder. Otherwise, it is considered an absolute path and is "
            "left unchanged.", "label"),
    ("Randomly space within chest?", False),
    ("For non-empty chests:", ("silent", "log", "alert", "add to", "overwrite")),
)



def perform(level, box, options):
    path = options["Loot script path:"]
    randomly_space = options["Randomly space within chest?"]
    non_empty = options["For non-empty chests:"]

    # Tidy up path.
    path = path.replace(os.path.sep, "/")
    if path.startswith("./"):
        here = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(here, path)
    path = os.path.abspath(path)
    path = path.replace("/", os.path.sep)

    print "Absolute path: {}".format(path)
    print "Randomly space: {}".format(randomly_space)
    print "Non-empty: {}".format(non_empty)


    # Parse the loot script.
    items = []
    with open(path, "r") as file:
        for i, line in enumerate(file):
            items += parse(line, i + 1)


    # Go through all the chests in selection.
    count = 0
    for teid, pos, te in br.iterate(level, box, br.TES):
        if teid not in {"Chest", "chest", "minecraft:chest"}:
            continue

        # Handle non-empty chests.
        if te["Items"]:
            s = "Non-empty chest at: {}".format(pos)
            if non_empty == "silent":
                continue
            elif non_empty == "log":
                print s
                continue
            elif non_empty == "alert":
                raise Exception(s)
            elif non_empty == "add to":
                pass
            elif non_empty == "overwrite":
                del te["Items"][:]

            # Fallthrough.

        count += 1

        # Shuffle to not have a fixed item order.
        rdm.shuffle(items)

        # Go through all the items.
        for item in items:
            # random is in the name yk.
            if rdm.random() > item.chance:
                continue

            # Get the slot to put it in.
            slot = next_slot(te["Items"], randomly_space)

            # Don't overfill the chest.
            if slot == 27:
                break
            te["Items"].append(item.nbt(slot))


    print("Added loot to {} chest{}.".format(count, "" if count == 1 else "s"))
    return



ALL_SLOTS = set(range(27))
def next_slot(items, randomly_space):
    # Get an array of the available slots in the chest.
    used_slots = set(map(lambda x: int(x["Slot"].value), items))
    free_slots = list(ALL_SLOTS - used_slots)

    # If there are no free slots, return an invalid slot (27) to indicate that.
    if not free_slots:
        return 27

    if randomly_space:
        # Randomly pick a slot.
        return rdm.choice(free_slots)
    else:
        # Otherwise use the top-left-most.
        return min(free_slots)



class Entry:
    def __init__(self, chance, item_id, item_data, amount, enchants):
        assert 0.0 <= chance and chance <= 1.0
        self.chance = chance
        self.item_id = item_id
        self.item_data = item_data
        self.amount = amount
        self.enchants = enchants

    def nbt(self, slot):
        assert slot in ALL_SLOTS

        # Do the compulsory item stuff.
        item = TAG_Compound()
        item["id"] = TAG_String(self.item_id)
        item["Damage"] = TAG_Short(self.item_data)
        item["Count"] = TAG_Byte(self.amount)
        item["Slot"] = TAG_Byte(slot)

        # Do item tag if it would have something in it (i.e. enchantments).
        if self.enchants:
            item["tag"] = TAG_Compound()
            item["tag"]["ench"] = TAG_List()
            for ench_id, ench_lvl in self.enchants:
                ench = TAG_Compound()
                ench["id"] = TAG_Short(ench_id)
                ench["lvl"] = TAG_Short(ench_lvl)
                item["tag"]["ench"].append(ench)

        return item



def parse(line, line_number):
    def throw(msg):
        raise Exception("Syntax error at line {}: {}".format(line_number, msg))

    def next_token(s):
        if not s:
            return s, ""

        # Ignore whitespace.
        if s[0].isspace():
            return s[1:], ""

        # Group alphanum.
        charset = "abcdefghijklmnopqrstuvwxyz0123456789_."
        if s[0] in charset:
            w = ""
            while s and s[0] in charset:
                w += s[0]
                s = s[1:]
            return s, w

        # Otherwise just give the character it's own group.
        return s[1:], s[0]

    def can_number(token):
        return all(c in "0123456789." for c in token)
    def can_integer(token):
        return all(c in "0123456789" for c in token)
    def can_string(token):
        return all(c in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in token)



    # Tokenise.
    tokens = []
    while line:
        line, t = next_token(line)
        if t:
            tokens.append(t)

    # Ignore empty lines or comments.
    if not tokens or tokens[0] == "#":
        return []

    # Check required args.
    if len(tokens) == 1:
        throw("need <item id> (and following args).")
    if len(tokens) == 2:
        throw("need <item data> (and following args).")
    if len(tokens) == 3:
        throw("need <amount>.")
    # ok if 4 or above.


    # Parse <percent_chance>.
    if not can_number(tokens[0]):
        throw("<percent_chance> must be a number.")
    chance = float(tokens[0]) / 100.0
    if chance < 0.0 or chance > 1.0:
        throw("<percent_chance> must be in 0..100.")

    # Prase <item_id>.
    if not can_string(tokens[1]):
        throw("<item_id> must be a string.")
    item_id = br.prefix(tokens[1])

    # Parse <item_data>.
    if not can_integer(tokens[2]):
        throw("<item_data> must be an integer.")
    item_data = int(tokens[2])
    if item_data < 0 or item_data > 32767:
        throw("<item_data> must be in 0..32767.")

    # Parse <amount>.
    if not can_integer(tokens[3]):
        throw("<amount> must be an integer.")
    amount = int(tokens[3])
    if amount < 0 or amount > 255:
        throw("<amount> must be in 0..255.")



    # Parse optional enchants.
    enchants = []
    tokens = tokens[4:] # consume the earlier args.
    while tokens:
        # Need to have <ench_id>:<ench_lvl> tokens.
        if len(tokens) < 3:
            throw("unfinished enchantment pair")

        # Parse <ench_id>.
        if not can_integer(tokens[0]):
            throw("<ench_id> must be an integer.")
        ench_id = int(tokens[0])

        # Ensure :
        if tokens[1] != ":":
            throw("invalid enchantment pair splitter.")

        # Parse <ench_lvl>.
        if not can_integer(tokens[2]):
            throw("<ench_lvl> must be an integer.")
        ench_lvl = int(tokens[2])
        if ench_lvl < 1 or ench_lvl > 32767:
            throw("<ench_lvl> must be in 1..32767.")

        # Add this enchanment.
        enchants.append((ench_id, ench_lvl))

        # Onto the next.
        tokens = tokens[3:]

    return [Entry(chance, item_id, item_data, amount, enchants)]
