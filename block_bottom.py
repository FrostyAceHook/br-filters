import time
from pymclevel import alphaMaterials

displayName = "Block Bop"

inputs = (
    ("Position:", ("Top", "Bottom")),
    ("Find except?", True),
    ("Find:", alphaMaterials.Air),
    ("Replace except?", False),
    ("Replace:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("For every \"find\" block in the selection, if the block above or below it satisfies the \"replace\" block, it is replaced with the \"block\" block.", "label")
)


def matches(is_except, block, level, x, y, z):
    level_block = (level.blockAt(x,y,z), level.blockDataAt(x,y,z))
    if is_except:
        return block != level_block
    else:
        return block == level_block


def perform(level, box, options):
    start = time.time()

    diff = 1 if options["Position:"]=="Top" else -1

    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    replace_except = options["Replace except?"]
    replace_block = (options["Replace:"].ID, options["Replace:"].blockData)

    find_except = options["Find except?"]
    find_block = (options["Find:"].ID, options["Find:"].blockData)

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

                # Gotta be in selection.
                if (x, y+diff, z) not in box:
                    continue

                # Gotta match the replace block.
                if not matches(replace_except, replace_block, level, x, y+diff, z):
                    continue

                level.setBlockAt(x, y+diff, z, block_id)
                level.setBlockDataAt(x, y+diff, z, block_data)

    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return