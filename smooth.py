import br
import numpy as np
from pymclevel import alphaMaterials, BoundingBox

displayName = "Smoother (brain)"

inputs = (
    ("Strength:", (3, 1, 20)),
    ("Void:", alphaMaterials.Air),
    ("Fill:", alphaMaterials.Stone),
    ("Replaces the selection with a smoothed version of the blocks. The filter "
            "analyses the selection as if it only contains two block types, "
            "\"void\" and not void. It then smoothes this hypothetical terrain "
            "and pastes it back into the level, filling any not void with "
            "\"fill\".", "label"),
    ("IT WILL DESTROY ANY BLOCK TYPE VARIATION", "label"),
)


# Smoothing algorithm:
# Works by literally replacing every block in the selection with the most common
# block around that particular block, effectively averaging out any outliers. The
# algorithm looks in a cube of radius `strength` around each block to determine
# the most common, this is mostly because it is ridiculously quick when
# implemented with numpy shifts and additions.


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

    # Copy to level.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        # Get the non-void mask of this slice.
        nv = non_void[slices]

        # Replace the non-void blocks.
        ids[nv] = fid
        datas[nv] = fdata

        # Replace the void blocks.
        ids[nv == False] = vid # double negative.
        datas[nv == False] = vdata


    # For a couple laughs just to break up the monotony, calculate a score of how
    # smooth the original blocks were.

    expanded, expanded_box = cache
    # Still need to correct the neighbour expansion.
    original = expanded[mask_from(expanded_box, box)]

    # Now get the absolute and proportional difference of the before and after.
    diff = np.sum(non_void != original)
    prop = float(diff) / box.volume

    # Cheeky score transform. It look kinda like this:
    # 100 |-,
    #     |  \
    #     |  |
    #     |   \
    #     |    \
    #   0 |     '--_____
    #     0     0.5     1
    # tremble at my ascii art powers.
    if prop > 0.02:
        score = 100.0 * (prop - 1.0)**8
    else:
        score = 100.0 - 2.3318278e11 * prop**6
    score = int(round(score))
    # Can't have too much fun now can we. Back to work.
    score = min(score, 99)

    print "You scored... {}!{}".format(score, " ...were you even trying?" if
            (score < 5) else "")

    print "Finished smoothing."
    return


def get_cache(level, box, strength, vid, vdata):
    # Need to expand the box to include `strength` extra blocks in all
    # directions, so that we can find the blocks in a `strength` radius around
    # every block in the actual selection. Aka, we don't need each house, we need
    # the whole neighbourhood.
    neighbourhood_box = box.expand(strength)


    # However, must ensure that we don't go out of bounds of the world. So check
    # all the chunks the box touches actually exist. Check first, with a
    # different message, that the actual selection doesn't contain missing
    # chunks.
    must_exist(level, box, "Selection cannot contain missing chunks.")
    must_exist(level, neighbourhood_box, "Selection is too close to missing "
            "chunks.")


    # We can just clamp the y axis instead of throwing if the selection grows too
    # tall. This clamping is dealt with in `smooth`, by assuming that the closest
    # layer is repeated out-of-bounds.
    x, _, z = neighbourhood_box.origin
    w, _, l = neighbourhood_box.size
    max_box = BoundingBox((x, 0, z), (w, 256, l))
    neighbourhood_box = neighbourhood_box.intersect(max_box)


    # Now cache which blocks are non-void.
    neighbourhood = np.empty(br.shape(neighbourhood_box), dtype=bool)
    for ids, datas, slices in br.iterate(level, neighbourhood_box,
            method=br.SLICES):
        # Add the non-void masks.
        neighbourhood[slices] = ((ids != vid) | (datas != vdata))

    return neighbourhood, neighbourhood_box



def smooth(cache, box, strength):
    neighbourhood, neighbourhood_box = cache

    # Need to replace every value with the sum of its neighbours, up to
    # `strength` blocks away. Cast to uint16 to be able to store that count.
    summed = neighbourhood.astype(np.uint16)


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


    # Cut the summed array from the neighbourhood shape to the user selection
    # box. Can't just hard-code strength:len-strength because the cache shape can
    # be unpredictable with clipping due to world boundaries.
    mask = mask_from(neighbourhood_box, box)
    summed = summed[mask]


    # To find which blocks should be non-void, we check if it has more neighbours
    # of non-void than not. That is, if the average block around this one is
    # non-void. This is simply a matter of checking if it's greater than half the
    # neighbour (cube) volume.
    cutoff = ((2 * strength + 1) ** 3) // 2
    non_void = (summed > cutoff)


    # Too easy.
    return non_void



# Throws if any chunks in the given box don't exist.
def must_exist(level, box, msg):
    for cx, cz in box.chunkPositions:
        if not level.containsChunk(cx, cz):
            raise Exception(msg)


# Returns a mask which may be applied to an array of the `neighbourhood_box`
# which will index the blocks in `box`.
def mask_from(neighbourhood_box, box):
    # We want to get the intersection of the two boxes, in a mark relative to the
    # neighbourhood. We know the neighboorhood is always larger, so the size of
    # final mask will be the same as `box`. So we can just shift the `box` to
    # have an origin at the origin of `neighbourhood` to find the indices we
    # need.
    mask_box = BoundingBox(box.origin - neighbourhood_box.origin, box.size)
    return br.box_slices(mask_box)
