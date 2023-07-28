import time
from pymclevel import alphaMaterials
import math

displayName = "Mark Centre"

inputs = (
    ("Block:", alphaMaterials.Glowstone),
    ("Replaces the very centre point of the selection with the block above. Used to quickly find the centre of something. If any dimension is even in length, two blocks are placed.", "label"),
)


# Why isnt this the default floor?
def ifloor(x):
    return int(math.floor(x))


def perform(level, box, options):
    start = time.time()

    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData


    # Find the exact middles.
    x = box.minx + box.width/2.0
    y = box.miny + box.height/2.0
    z = box.minz + box.length/2.0

    # Find the integer middles.
    x = [ifloor(x)] if box.width%2 else [ifloor(x) - 1, ifloor(x)]
    y = [ifloor(y)] if box.height%2 else [ifloor(y) - 1, ifloor(y)]
    z = [ifloor(z)] if box.length%2 else [ifloor(z) - 1, ifloor(z)]

    # Mark the centre.
    for cx in x:
        for cy in y:
            for cz in z:
                level.setBlockAt(cx, cy, cz, block_id)
                level.setBlockDataAt(cx, cy, cz, block_data)


    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return