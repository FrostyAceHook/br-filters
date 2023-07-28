import time
import numpy as np

displayName = "Smooth (brain)"

inputs = (
    ("Smoothing strength:", (3, 1, 100)),
    ("Mask:", ("sphere", "cube", "diamond")),
    ("Smooths the selection. Very slow with large smooth strengths (>10). Recommended to use on a single block type then do variations later as it will mess up the distribution of block types.", "label")
)


# Smoothing algorithm:
# Works by literally replacing every block in the selection with the most common
# block around that particular block, effectively averaging out any outliers.



def perform(level, box, options):
    start = time.time()

    smoothing = options["Smoothing strength:"]
    shape = options["Mask:"]


    print("Caching (all me bitch).")
    # Cache of blocks, in x,z,y order where 0,0,0 is the minimum corner of the
    # box, minus smoothing in all dimensions. Significantly speeds things up
    # since it's using numpy access as opposed to slow pythonic access.
    cache = get_cache(level, box.expand(smoothing))

    # Masking indices, in x,z,y order.
    mask = get_mask(smoothing, shape)


    print("Smoothing.")
    print("Total y: {}".format(box.height))
    for y in xrange(box.height):
        if y%5 == 0:
            print("y: {}".format(y))
        for x in xrange(box.width):
            for z in xrange(box.length):
                # Shift mask.
                mask[0,:] += x
                mask[1,:] += z
                mask[2,:] += y

                # Get the most frequent block that occurs within the mask at this position.
                block_id, block_data = get_block(np.bincount(cache[tuple(mask)]).argmax())

                # Unshift mask.
                mask[0,:] -= x
                mask[1,:] -= z
                mask[2,:] -= y

                # Set the block.
                level.setBlockAt(box.minx + x, box.miny + y, box.minz + z, block_id)
                level.setBlockDataAt(box.minx + x, box.miny + y, box.minz + z, block_data)


    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return


def get_cache(level, box):
    # Fortran order makes it *slightly* faster when moving block data from chunk to cache.
    blocks = np.empty((box.width, box.length, box.height, 2), dtype=np.uint16, order='F')

    for chunk, slices, point in level.getChunkSlices(box):
        # Translation from chunk slices to cache slices.
        translate = tuple(chunk.bounds.origin[i] - box.origin[i] for i in (0,2,1))
        cache_slices = [slice(s.start + t, s.stop + t) for s,t in zip(slices, translate)]

        blocks[
                cache_slices[0],
                cache_slices[1],
                cache_slices[2],
                0
            ] = chunk.Blocks[slices]
        blocks[
                cache_slices[0],
                cache_slices[1],
                cache_slices[2],
                1
            ] = chunk.Data[slices]

    # numpy trickery to view the 4th dimension of (id, data) as one merged integer.
    return blocks.reshape(blocks.shape[0], blocks.shape[1], -1).view(np.uint32)


def get_mask(smoothing, shape):
    # x,z,y order.
    mask = []
    for dx in xrange(-smoothing, smoothing):
        for dz in xrange(-smoothing, smoothing):
            for dy in xrange(-smoothing, smoothing):
                # Make shape.
                if shape == "sphere":
                    if dx*dx + dy*dy + dz*dz > smoothing*smoothing:
                        continue
                elif shape == "diamond":
                    if dx + dy + dz > smoothing:
                        continue
                # "cube" has no coords culled.

                mask.append([dx + smoothing, dz + smoothing, dy + smoothing])

    indices = np.array(mask).T
    return indices


def get_block(value):
    bid = value & 0xFFFF
    bdata = (value >> 16) & 0xFFFF
    return bid, bdata
