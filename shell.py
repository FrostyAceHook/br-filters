import time
from pymclevel import alphaMaterials

displayName = "Fill Shell"

inputs = (
    ("Block:", alphaMaterials.Bedrock),
    ("Cheeky bedrock box filter. If used with a selection where one dimension has 1 length, it will make a ring.", "label"),
)


def perform(level, box, options):
    start = time.time()

    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    width = box.maxx-box.minx
    height = box.maxy-box.miny
    length = box.maxz-box.minz

    # Check if it needs to be a ring.
    do_ring = False
    for dim in (width, height, length):
        if dim == 1:
            if do_ring:
                raise Exception("Cannot have a selection with more than one dimension length of 1.")
            do_ring = True

    if do_ring:
        ring(level, box, block_id, block_data)
    else:
        shell(level, box, block_id, block_data)

    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return



def shell(level, box, block_id, block_data):
    # z top and bottom.
    for x in xrange(box.minx, box.maxx):
        for y in xrange(box.miny, box.maxy):
            level.setBlockAt(x, y, box.minz, block_id)
            level.setBlockDataAt(x, y, box.minz, block_data)

            level.setBlockAt(x, y, box.maxz-1, block_id)
            level.setBlockDataAt(x, y, box.maxz-1, block_data)

    # y top and bottom.
    for x in xrange(box.minx, box.maxx):
        for z in xrange(box.minz, box.maxz):
            level.setBlockAt(x, box.miny, z, block_id)
            level.setBlockDataAt(x, box.miny, z, block_data)

            level.setBlockAt(x, box.maxy-1, z, block_id)
            level.setBlockDataAt(x, box.maxy-1, z, block_data)

    # x top and bottom.s
    for y in xrange(box.miny, box.maxy):
        for z in xrange(box.minz, box.maxz):
            level.setBlockAt(box.minx, y, z, block_id)
            level.setBlockDataAt(box.minx, y, z, block_data)

            level.setBlockAt(box.maxx-1, y, z, block_id)
            level.setBlockDataAt(box.maxx-1, y, z, block_data)
    return


def ring(level, box, block_id, block_data):
    width = box.maxx-box.minx
    height = box.maxy-box.miny
    length = box.maxz-box.minz

    # ew. im sorry you have to see this.

    if width == 1:
        for y in xrange(box.miny, box.maxy):
            level.setBlockAt(        box.minx,    y,    box.minz,    block_id)
            level.setBlockDataAt(    box.minx,    y,    box.minz,    block_data)

            level.setBlockAt(        box.minx,    y,    box.maxz-1,    block_id)
            level.setBlockDataAt(    box.minx,    y,    box.maxz-1,    block_data)

        for z in xrange(box.minz, box.maxz):
            level.setBlockAt(        box.minx,    box.miny,    z,    block_id)
            level.setBlockDataAt(    box.minx,    box.miny,    z,    block_data)

            level.setBlockAt(        box.minx,    box.maxy-1,    z,    block_id)
            level.setBlockDataAt(    box.minx,    box.maxy-1,    z,    block_data)

    elif height == 1:
        for x in xrange(box.minx, box.maxx):
            level.setBlockAt(        x,    box.miny,    box.minz,    block_id)
            level.setBlockDataAt(    x,    box.miny,    box.minz,    block_data)

            level.setBlockAt(        x,    box.miny,    box.maxz-1,    block_id)
            level.setBlockDataAt(    x,    box.miny,    box.maxz-1,    block_data)

        for z in xrange(box.minz, box.maxz):
            level.setBlockAt(        box.minx,    box.miny,    z,    block_id)
            level.setBlockDataAt(    box.minx,    box.miny,    z,    block_data)

            level.setBlockAt(        box.maxx-1,    box.miny,    z,    block_id)
            level.setBlockDataAt(    box.maxx-1,    box.miny,    z,    block_data)

    elif length == 1:
        for x in xrange(box.minx, box.maxx):
            level.setBlockAt(        x,    box.miny,    box.minz,    block_id)
            level.setBlockDataAt(    x,    box.miny,    box.minz,    block_data)

            level.setBlockAt(        x,    box.maxy-1,    box.minz,    block_id)
            level.setBlockDataAt(    x,    box.maxy-1,    box.minz,    block_data)

        for y in xrange(box.miny, box.maxy):
            level.setBlockAt(        box.minx,    y,    box.minz,    block_id)
            level.setBlockDataAt(    box.minx,    y,    box.minz,    block_data)

            level.setBlockAt(        box.maxx-1,    y,    box.minz,    block_id)
            level.setBlockDataAt(    box.maxx-1,    y,    box.minz,    block_data)
    return