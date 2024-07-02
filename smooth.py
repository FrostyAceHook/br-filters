import br
import numpy as np
from pymclevel import alphaMaterials, BoundingBox

displayName = "Smoother (brain)"

inputs = (
    ("Replaces the selection with a smoothed version of the blocks. Within and "
            "up-to 'strength' blocks outside of the selection, there must be at-"
            "most two different blocks.", "label"),
    ("Strength:", (3, 1, 15)),
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

    # Copy the selection blocks + surrounding blocks to a cache.
    cache, blocks = get_cache(level, box, strength)

    # Get the palette of blocks.
    if len(blocks) == 1:
        print "Selection only has one block type, no smoothing to perform."
        return
    assert len(blocks) == 2
    vid, vdata = blocks[0]
    nvid, nvdata = blocks[1]


    # Get the smoothed blocks. This is a boolean array where true = non-void.
    non_void = smooth(cache, box, strength)

    # Copy to level.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        # Get the non-void mask of this slice.
        nv = non_void[slices]

        # Replace the non-void blocks.
        ids[nv] = nvid
        datas[nv] = nvdata

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



def get_cache(level, box, strength):
    # Need to expand the box to include `strength` extra blocks in all
    # directions, so that we can find the blocks in a `strength` radius around
    # every block in the actual selection. Aka, we don't need each house, we need
    # the whole neighbourhood.
    neighbourhood_box = box.expand(strength)

    # We can just clamp the y axis instead of throwing if the selection grows too
    # tall. This clamping is dealt with in `smooth` when shifting, by assuming
    # that the closest layer is repeated out-of-bounds.
    x, _, z = neighbourhood_box.origin
    w, _, l = neighbourhood_box.size
    max_box = BoundingBox(origin=(x, 0, z), size=(w, 256, l))
    neighbourhood_box = neighbourhood_box.intersect(max_box)


    # However, must ensure that we don't go out of bounds of the world. So check
    # all the chunks the box touches actually exist. Check first, with a
    # different message, that the actual selection doesn't contain missing
    # chunks.
    must_exist(level, box, "Selection cannot contain missing chunks.")
    must_exist(level, neighbourhood_box, "Selection is too close to missing "
            "chunks.")


    # We need to pick one block to act as the "void" block. The operation is
    # "symmetrical" with respect to this block so it doesn't matter what we
    # choose.
    vid = level.blockAt(*box.origin)
    vdata = level.blockDataAt(*box.origin)


    # The unique blocks in the level, stored as a set of tuples of (bid, bdata).
    # I think the bid and bdata are of type np.uint16 not int but it doesn't
    # really matter.
    unique_blocks = set()

    # Now cache which blocks are non-void.
    neighbourhood = np.empty(br.shape(neighbourhood_box), dtype=bool)
    for ids, datas, slices in br.iterate(level, neighbourhood_box, br.BLOCKS):
        # Get a list of all the blocks in this iteration.
        blocks = np.stack((ids, datas), axis=-1)
        blocks = blocks.reshape(-1, 2)
        # Now axis=0 goes along the blocks and axis=1 stores the bid, bdata.

        # However, since this version of numpy doesn't have an axis argument for
        # `unique`, we gotta roll our own.

        # Treat the rows of bid,bdata pairs as a single element.
        merged_dtype = np.dtype((np.void, 2 * blocks.dtype.itemsize))
        merged_blocks = blocks.view(merged_dtype)

        # Find the unique blocks.
        unique = np.unique(merged_blocks)

        # Convert back to the unpacked view.
        unique = unique.view(blocks.dtype).reshape(-1, 2)

        # Add the unique blocks. Note we convert to a tuple to make it hashable.
        unique_blocks |= set((bid, bdata) for bid, bdata in unique)

        # Add the non-void masks.
        neighbourhood[slices] = ((ids != vid) | (datas != vdata))

    # If there are more than 2 blocks in the selection, no can do.
    if len(unique_blocks) > 2:
        raise Exception("Selection has more than 2 block types.")


    cache = neighbourhood, neighbourhood_box

    # We also gotta return the blocks used.
    if len(unique_blocks) == 2:
        unique_blocks -= {(vid, vdata)} # remove the void block.
        blocks = (vid, vdata), next(iter(unique_blocks))
    else:
        # No second block.
        blocks = ((vid, vdata), )

    return cache, blocks



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


    # Cut the array from the neighbourhood shape to the user selection box.
    # Can't just hard-code strength:len-strength because the cache shape can be
    # unpredictable with clipping due to world boundaries.
    mask = mask_from(neighbourhood_box, box)
    summed = summed[mask]


    # To find which blocks should be non-void, we check if it has more neighbours
    # of non-void than not. That is, if the average block around this one is
    # non-void. This is simply a matter of checking if it's greater than half the
    # neighbour (cube) volume. Note that this will always be an odd number, so we
    # can always get a clean majority.
    cutoff = ((2*strength + 1) ** 3) // 2
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
