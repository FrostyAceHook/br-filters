import time
from pymclevel import alphaMaterials
import random as rdm

displayName = "Top Soil"

inputs = (
    ("Find except?", False),
    ("Find:", alphaMaterials.Air),
    ("Replace except?", True),
    ("Replace:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("Min depth:", (2, 1, 256)),
    ("Max depth:", (4, 1, 256)),
    ("For every \"find\" block in the selection, replaces a random number between \"min\" and \"max\" of \"replace\" blocks beneath it with \"block\".","label"),
)


def matches(is_except, block, level, x, y, z):
    level_block = (level.blockAt(x,y,z), level.blockDataAt(x,y,z))
    if is_except:
        return block != level_block
    else:
        return block == level_block


def perform(level, box, options):
    start = time.time()

    depth_min = options["Min depth:"]
    depth_max = options["Max depth:"]

    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    replace_except = options["Replace except?"]
    replace_block = (options["Replace:"].ID, options["Replace:"].blockData)

    find_except = options["Find except?"]
    find_block = (options["Find:"].ID, options["Find:"].blockData)

    # Track every block to be placed until the entire selection is searched. This
    # is so that replacing the blocks mid operation doesn't lead to an entire
    # column being filled because the filter fulfills itself.
    coord_cache = set()

    if depth_max < depth_min:
        raise Exception("Min depth must be less than max depth.")

    # Do the thing.
    print("Total y: {}".format(box.height))
    # Going bottom to top i think makes it faster yeah?? idk who cares.
    for y in xrange(box.height):
        if y%5 == 0:
            print("y: {}".format(y))
        y += box.miny
        for x in xrange(box.minx, box.maxx):
            for z in xrange(box.minz, box.maxz):
                # Gotta match the find block.
                if not matches(find_except, find_block, level, x, y, z):
                    continue

                # Depth of this block.
                depth = rdm.randint(depth_min, depth_max)

                # While it matches the replace and it's in bounds, add it.
                for i in range(1, depth + 1):
                    p = (x, y-i, z)
                    # Check bounds.
                    if p not in box:
                        break
                    # Check block.
                    if not matches(replace_except, replace_block, level, *p):
                        break
                    # Add to cache.
                    coord_cache.add(p)

    # Set all the blocks in the cache.
    for x,y,z in coord_cache:
        level.setBlockAt(x, y, z, block_id)
        level.setBlockDataAt(x, y, z, block_data)

    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return