import time
from pymclevel import alphaMaterials

displayName = "Gridify 2"

inputs = (
    ("Find except?", True),
    ("Find:", alphaMaterials.Air),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 2:", alphaMaterials.Cobblestone),
    ("Swap blocks?", False),
    ("issa grid innit. Swap blocks is a purely convenience option.", "label"),
)


def matches(is_except, block, level, x, y, z):
    level_block = (level.blockAt(x,y,z), level.blockDataAt(x,y,z))
    if is_except:
        return block != level_block
    else:
        return block == level_block


def perform(level, box, options):
    start = time.time()

    block_id = (options["Block 1:"].ID, options["Block 2:"].ID)
    block_data = (options["Block 1:"].blockData, options["Block 2:"].blockData)

    find_except = options["Find except?"]
    find_block = (options["Find:"].ID, options["Find:"].blockData)

    # Do the thang.
    print("Total y: {}".format(box.height))
    for y in xrange(box.height):
        if y%5 == 0:
            print("y: {}".format(y))
        y += box.miny
        for x in xrange(box.minx, box.maxx):
            for z in xrange(box.minz, box.maxz):

                # Gotta match the find block.
                if not matches(find_except, find_block, level, x, y, z):
                    continue

                # Cheekily incorperate the swap option.
                is_odd = (x + y + z + int(options["Swap blocks?"]))%2

                level.setBlockAt(x, y, z, block_id[is_odd])
                level.setBlockDataAt(x, y, z, block_data[is_odd])


    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return