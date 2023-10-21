from itertools import product
from pymclevel import alphaMaterials

displayName = "Mark Centre"

inputs = (
    ("Block:", alphaMaterials.Glowstone),
    ("Replaces the very centre point of the selection with the block above. Used to quickly find the centre of something. If any dimension is even in length, two blocks are placed.", "label"),
)


def perform(level, box, options):
    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    # Find the floored middle.
    x = box.minx + box.width /2
    z = box.minz + box.length/2
    y = box.miny + box.height/2

    # Find the actual middles.
    X = [x] if (box.width  % 2) else [x - 1, x]
    Z = [z] if (box.length % 2) else [z - 1, z]
    Y = [y] if (box.height % 2) else [y - 1, y]

    # Mark the centre.
    for cx, cz, cy in product(X, Z, Y):
        level.setBlockAt(cx, cy, cz, block_id)
        level.setBlockDataAt(cx, cy, cz, block_data)


    level.markDirtyBox(box)
    print "Finished marking centre."
    return