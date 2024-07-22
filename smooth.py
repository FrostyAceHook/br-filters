import numpy as np
from itertools import product
from pymclevel import alphaMaterials, BoundingBox

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you downloaded it and put it "
            "in the same filter folder?")


displayName = "Smoothest (brain)"

inputs = (
    ("Replaces the selection with a smoothed version of the blocks. Within and "
            "up-to 'strength' blocks outside of the selection, there must be at-"
            "most two different blocks. When feathering, the edges of the "
            "selection will attempt to more smoothly join to the blocks outside "
            "of the selection.", "label"),
    ("Strength:", (3, 1, 15)),
    ("Feather?", False),
)


# Smoothing algorithm:
# Works by literally replacing every block in the selection with the most common
# block around that particular block, effectively averaging out any outliers. The
# algorithm looks in a cube of radius `strength` around each block to determine
# the most common, this is mostly because it is ridiculously quick when
# implemented with numpy shifts and additions.


def perform(level, box, options):
    strength = options["Strength:"]
    feather = options["Feather?"]

    print "Strength: {}".format(strength)
    print "Feather: {}".format(feather)

    # Copy the selection blocks + surrounding blocks.
    cache, blocks = extract(level, box, strength)

    # Get the palette of blocks.
    if len(blocks) == 1:
        print "Selection only has one block type, no smoothing to perform."
        return
    assert len(blocks) == 2
    vid, vdata = blocks[0]
    nvid, nvdata = blocks[1]


    # Get the smoothed blocks. This is a boolean array where true = non-void.
    non_void = smooth(cache, box, strength, feather)

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



def extract(level, box, strength):
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
        raise Exception("Selection/surroundings have more than 2 block types.")


    cache = neighbourhood, neighbourhood_box

    # We also gotta return the blocks used.
    if len(unique_blocks) == 2:
        unique_blocks -= {(vid, vdata)} # remove the void block.
        blocks = (vid, vdata), next(iter(unique_blocks))
    else:
        # No second block.
        blocks = ((vid, vdata), )

    return cache, blocks



def smooth(cache, box, strength, feather):
    neighbourhood, neighbourhood_box = cache

    # Need to replace every value with the sum of its neighbours, up to
    # `strength` blocks away. Cast to uint16 to be able to store that count.
    summed = neighbourhood.astype(np.uint16)


    # Preallocate some memory.
    tmp1 = np.empty_like(summed)
    tmp2 = np.empty_like(summed)

    if not feather:

        # Sum in a cube around each block.
        sum_cube(summed, strength, tmp1, tmp2)

        # To find which blocks should be non-void, we check if it has more
        # neighbours of non-void than not. That is, if the average block around
        # this one is non-void. This is simply a matter of checking if it's
        # greater than half the neighbour (cube) volume. Note that this will always
        # be an odd number, so we can always get a clean majority.
        cutoff = ((2*strength + 1) ** 3) // 2
        non_void = (summed > cutoff)

    else:
        # If we are feathering, we want the smooth strength to linearly increase
        # from 1 to its maximum (`strength`) when going from the outside inwards.
        # Essentially, shells of increasing smooth radius.

        non_void = np.empty(summed.shape, dtype=bool)

        # The smoothed array for the current smooth radius.
        this = np.empty_like(summed)

        # Build up to the full smooth strength.
        for size in range(1, strength + 1):
            # Do this iteration of smooth strength.
            this[:] = summed
            sum_cube(this, size, tmp1, tmp2)
            cutoff = ((2*size + 1) ** 3) // 2

            # Gotta do some awkward logic to get the slices of the current
            # iteration's box (which shirnks by 1 every iteration).
            inset_by = size - 1
            slices = mask_from(neighbourhood_box, box)
            slices = tuple(
                slice(s.start + inset_by, s.stop - inset_by)
                for s in slices
            )

            # Set this section. Note this always includes the centre, so while
            # early iterations will affect more than just a shell, the inside
            # will be overwritten by later ones so the overall effect is a shell.
            non_void[slices] = (this > cutoff)[slices]


    # Cut the array from the neighbourhood shape to the user selection box. Can't
    # just hard-code strength:len-strength because the cache shape can be
    # unpredictable with clipping due to world boundaries.
    mask = mask_from(neighbourhood_box, box)
    non_void = non_void[mask]

    # Too easy.
    return non_void



def sum_cube(array, size, tmp1, tmp2):
    # Simple algorithm to in-place sum in a cube of radius `size` around each
    # cell.

    # Across axes, a stack-on effect is desired.
    for axis in br.AXES:
        # Within an axis however, that stack-on would make a non-linear sum.
        tmp1[:] = array
        for by in range(-size, size + 1):
            if by == 0: # don't double-count indices with themselves.
                continue
            # Add the neighbours, using clamp to avoid excessively filling void
            # around the world top/bottom (instead assuming the closest layer was
            # repeated out of bounds).
            array += br.shift(tmp1, by, axis, clamp=True, out=tmp2)



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
    assert all(a >= b for a, b in zip(neighbourhood_box.size, box.size))
    mask_box = BoundingBox(box.origin - neighbourhood_box.origin, box.size)
    return br.slices(mask_box)
