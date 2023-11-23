import br
from itertools import chain
from collections import OrderedDict
from math import floor
from pymclevel import TileEntity, Entity

displayName = "Find"

# Trapped chests literally just use the chest tile entity...

# Create the maps from name to the possible ids. The ids are for pre/post 1.11.

BLOCK_IDS = OrderedDict([
    ("chest", {"Chest", "minecraft:chest"}),
    ("furnace", {"Furnace", "minecraft:furnace"}),
    ("dispenser", {"Trap", "minecraft:dispenser"}),
    ("dropper", {"Dropper", "minecraft:dropper"}),
    ("hopper", {"Hopper", "minecraft:hopper"}),
    ("brewing stand", {"Cauldron", "minecraft:brewing_stand"}), # ??? y cauldron
])

ENTITY_IDS = OrderedDict([
    ("item frame", {"ItemFrame", "minecraft:item_frame"}),
    ("minecart chest", {"MinecartChest", "minecraft:chest_minecart"}),
    ("minecart hopper", {"MinecartHopper", "minecraft:hopper_minecart"}),
])

# Pluralise and add a colon.
def to_option(name):
    return "{}s:".format(name.capitalize())


inputs = (
    ("Check the console for the results. The item id doesn't need the \"minecraft:\".", "label"),
    ("Item id:", "string"),
    ("Item data:", (0, 0, 32767)),
    ("Print every location:", True),
    ("Find in ...", "label"),
)
# Add the container options.
inputs += tuple((to_option(name), True) for name in chain(BLOCK_IDS, ENTITY_IDS))
# Let em know about the trapped chests.
inputs += ("Note that trapped chest are not distinguished from regular chests (to emulate gameplay of course (actually bc they use the same tile entity)).", "label"),

def perform(level, box, options):
    find = prefix(options["Item id:"]), options["Item data:"]
    print "Finding ({}, {}) ...".format(*find)

    print_each_storage = options["Print every location:"]


    # Setup which storages to check.
    block_ids = set()
    for name in BLOCK_IDS:
        if options[to_option(name)]:
            block_ids |= BLOCK_IDS[name]

    entity_ids = set()
    for name in ENTITY_IDS:
        if options[to_option(name)]:
            entity_ids |= ENTITY_IDS[name]


    # Total counts of what's been found.
    total_count = 0
    storage_count = 0

    # Iterate through the storages, printing when something is found.
    for name, pos, items in storages(level, box, block_ids, entity_ids):
        # Count how many items match.
        count = 0
        for item in items:
            item_id = prefix(item["id"].value)
            item_damage = item["Damage"].value
            if (item_id, item_damage) != find:
                continue

            count += item["Count"].value

        # Print matches, if any.
        if count > 0:
            total_count += count
            storage_count += 1

            # Format: "[chest] (0,64,0): 5", meaning found 5 items in the chest
            # at x=0, y=64, z=0.
            # This may not be the optimal way of the viewing the data (you may
            # want to sort by x, by z, by count, by something), but just like
            # copy it to a spreadsheet at that point. This is just to gen the
            # data.
            if print_each_storage:
                print "[{}] {}: {}".format(name, pos, count)


    # Print total count.
    if total_count > 0:
        print "Found {} total, across {} storage{}.".format(total_count,
                storage_count, "s" if storage_count != 1 else "")
    else:
        print "Not found."

    return



# Make an id to name map.
ALL_IDS = chain(BLOCK_IDS.items(), ENTITY_IDS.items())
NAMES = {eid: name for name, eids in ALL_IDS for eid in eids}


# Yeilds the name, position and items of every storage in the selection, filtered
# to only `block_ids` and `entity_ids`. The position is in xyz order.
def storages(level, box, block_ids, entity_ids):
    # Find the items in the blocks.
    for eid, pos, te in br.iterate(level, box, method=br.TES):
        # Gotta be a storage that's getting checked.
        if eid not in block_ids:
            continue

        # Gotta have items dunnit. This is basically just to skip malformed tile
        # entities,
        if "Items" not in te:
            continue

        # Same item api for all (supported) storage types.
        yield NAMES[eid], pos, te["Items"]


    # Find the items in the entities.
    for eid, pos, entity in br.iterate(level, box, method=br.ENTITIES):
        # Gotta be a storage that's getting checked.
        if eid not in entity_ids:
            continue


        # Item frame stores it differently :c.
        if eid in ENTITY_IDS["item frame"]:
            # Gotta have items. This actually is an optional tag, doesn't
            # indicate a malformed entity.
            if "Item" not in entity:
                continue
            # make iterable.
            items = (entity["Item"],)

        # Otherwise stores multiple items (w same api).
        else:
            if "Items" not in entity:
                continue
            items = entity["Items"]


        # Just return the block position. Use floor to match up w minecraft.
        ipos = tuple(int(floor(x)) for x in pos)

        yield NAMES[eid], ipos, items


# Add the "minecraft:" prefix if not present. In theory, everything should
# already have this but better be safe then sorry (intentional).
def prefix(item_id):
    if not item_id.startswith("minecraft:"):
        item_id = "minecraft:" + item_id
    return item_id
