import br
import numpy as np
from pymclevel import alphaMaterials, BoundingBox

displayName = "Smoother (brain)"

inputs = (
    ("Strength:", (3, 1, 20)),
    ("Void:", alphaMaterials.Air),
    ("Fill:", alphaMaterials.Stone),
    ("Replaces the selection with a smoothed version of the blocks. The filter analyses the selection as if it only contained two block types, \"void\" and not void. It then smoothes this hypothetical terrain and pastes it back into the level, filling any not void with \"fill\".", "label"),
    ("IT WILL DESTROY ANY BLOCK TYPE VARIATION", "label"),
)


# Smoothing algorithm:
# Works by literally replacing every block in the selection with the most common
# block around that particular block, effectively averaging out any outliers.


def perform(level, box, options):
    strength = options["Strength:"]

    print "Strength: {}".format(strength)

    # Get the void and fill blocks.
    vid, vdata = options["Void:"].ID, options["Void:"].blockData
    fid, fdata = options["Fill:"].ID, options["Fill:"].blockData

    # Cache the selection.
    cache = get_cache(level, box, strength, vid, vdata)

    # Get the smoothed blocks. This is a boolean array where true = non-void.
    non_void = smooth(cache, box, strength)

    # Convert to actual block values.
    bids = np.empty(non_void.shape, dtype=np.uint16)
    bdatas = np.empty_like(bids)

    # Replace the non-void blocks.
    bids[non_void] = fid
    bdatas[non_void] = fdata

    # Replace the void blocks.
    bids[non_void == False] = vid # double negative.
    bdatas[non_void == False] = vdata

    # Copy to level.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        ids[:] = bids[slices]
        datas[:] = bdatas[slices]

    level.markDirtyBox(box)
    print "Finished smoothing."
    return


def get_cache(level, box, strength, vid, vdata):
    # Need to expand the box to include `strength` extra blocks in all
    # directions, so that we can find the blocks in a `strength` radius around
    # every block in the actual selection.
    box = box.expand(strength)


    # However, must ensure that we don't go out of bounds of the world. So check
    # all the chunks the box touches actually exist.
    for cx, cz in box.chunkPositions:
        if not level.containsChunk(cx, cz):
            raise Exception("Selection is too close to missing chunks.")


    # We can just clamp the y axis. This clamping is dealt with in `smooth`, by
    # assuming that the closest layer is repeated out-of-bounds.
    if box.miny < 0:
        box = BoundingBox((box.minx, 0, box.minz), box.size)
    if box.maxy > 256:
        box = BoundingBox(box.origin, (box.size.x, 256 - box.miny, box.size.z))


    # Now cache which blocks are non-void.
    sel = np.empty(br.shape(box), dtype=bool)
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        # Add the non-void masks.
        sel[slices] = ((ids != vid) | (datas != vdata))

    return sel, box



def smooth(cache, box, strength):
    # Unpack the cache into the selection mask and its bounding box.
    sel, sel_box = cache

    # Need to replace every value with the sum of its neighbours, up to
    # `strength` blocks away. Cast to uint16 to be able to store that count.
    summed = sel.astype(np.uint16)


    # Preallocate the memory.
    mem = np.empty_like(summed)
    unshifted = np.empty_like(summed)

    # Simple algorithm to sum in a cube around each point.
    for axis in br.AXES:
        # Need to copy before shifting along this axis to prevent a stack-on
        # effect where past shifts are repeated.
        unshifted[:] = summed
        for by in range(-strength, strength + 1):
            if by == 0:
                continue
            # Add the neighbours, using clamp to avoid excessively filling void
            # around the world top/bottom (instead assuming the closest layer was
            # repeated out of bounds).
            summed += br.shift(unshifted, by, axis, clamp=True, out=mem)


    # Cut the summed array from the cache shape to the user selection shape.
    # Can't just hard-code strength:len-strength because the cache shape can be
    # unpredictable with clipping due to world boundaries.
    box = BoundingBox(box.origin - sel_box.origin, box.size)
    mask = br.box_slices(box)

    # Do the cut.
    summed = summed[mask]


    # To find which blocks should be non-void, we check if it has more neighbours
    # of non-void than not. That is, if the average block around this one is
    # non-void. This is simply a matter of checking if it's greater than half the
    # neighbour (cube) volume.
    cutoff = ((2 * strength + 1) ** 3) // 2
    non_void = (summed > cutoff)


    # Too easy.
    return non_void
