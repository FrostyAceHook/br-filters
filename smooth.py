import numpy as np
from itertools import product
from pymclevel import alphaMaterials, BoundingBox

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you put it in the same "
            "filter folder? It can be downloaded from: "
            "github.com/FrostyAceHook/br-filters")
try:
    br.require_version(2, 2)
except AttributeError:
    raise ImportError("Outdated version of 'br.py'. Please download the latest "
            "compatible version from: github.com/FrostyAceHook/br-filters")


displayName = "Smooth"


inputs = (
    ("Replaces the selection with a smoothed version of the blocks. When "
            "feathering, the edges of the selection will attempt to more "
            "smoothly join to the blocks outside of the selection.", "label"),
    ("Note that this WILL mess up any block variation.", "label"),
    ("Strength:", (3, 1, 16)),
    ("Feather?", True),
)

count_type = np.uint16 # up-to 64k volume.



# Smoothing algorithm:
# Works by literally replacing every block in the selection with the most common
# block around that particular block, effectively averaging out any outliers. The
# algorithm looks in a cube of radius `strength` around each block to determine
# the most common, this is mostly because it is ridiculously quick when
# implemented with numpy shifts and additions.


def perform(level, box, options):
    strength = options["Strength:"]
    feather = options["Feather?"]


    if not feather:
        # If no feather, simple call to `smooth`.
        smooth(level, box, strength=strength)
    else:
        # Otherwise we gotta pull a nasty feather algo on this bitch. The
        # algorithm is:
        # - run the full smooth everywhere EXCEPT leave a "deadmans" space
        #       around the edges of the selection.
        # - this space has a depth of `strength-1` blocks.
        # - in shells starting from the already-smoothed area, runs smooths of
        #       steadily decreasing strength.
        # - these shell stack on-top of each other and creep towards the bounds
        #       of selection.
        # - all shells operate after the previous smooth is complete, they "see"
        #       the block changes it produces.
        # - eventually, the outer-most shell will be smoothed with strength 1.
        # - done.

        # Rename these things.
        full_box = box
        full_strength = strength

        # The shells must have "time" to drop to a smooth strength of 1, so this
        # is the inverse calc to ensure it can.
        strength = min(full_strength, min((x + 1)/2 for x in full_box.size))

        # Setup the mask array for smooth, initially all blocks are included.
        mask = np.ones(br.shape(full_box), dtype=bool)

        # Complete the full smooth on the inside section.
        box = full_box.expand(-strength + 1) # shrink.
        smooth(level, box, strength=strength)

        # Now iterate through the shells, inner-most to outer-most.
        for s in range(strength - 1, 0, -1):
            # Maks out the earlier smooths.
            mask[br.submask(full_box, box)] = False
            # Include this shell's mask.
            box = box.expand(1)
            shell = mask[br.submask(full_box, box)]

            # SHMOOTH
            smooth(level, box, strength=s, mask=shell)

        # Restore the thangs for logging purposes.
        strength = full_strength
        box = full_box


    # For a couple laughs just to break up the monotony, calculate a score of how
    # smooth the original blocks were.
    # NO. no cheeky laughs to break up the monotony. back to work.

    print "Finished smoothing:"
    print "- strength: {}".format(strength)
    print "- feather: {}".format(feather)
    return



# Performs a smooth of `strength` over `box`. If `mask` is non-none, it is a
# boolean mask of blocks to modify.
def smooth(level, box, strength, mask=None):
    # Get the neighbourhood box, which includes some extra blocks in each
    # direction.
    nbh = get_neighbourhood(level, box, strength)

    # Cache all the blocks and their locations.
    blocks = extract(level, nbh)

    # "Smear" the blocks to their surrounding, effectively "smoothing" the
    # blocks.
    smear(blocks, strength)

    # Extract the most common block at each location.
    bids, bdatas = most_common(blocks)

    # Trim the new blocks to the selection, instead of the entire neighbourhood.
    bids = bids[br.submask(nbh, box)]
    bdatas = bdatas[br.submask(nbh, box)]

    # Set the blocks. Not holey because the rest of the algorithm cant be.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        if mask is not None:
            # Use the mask if supplied.
            m = mask[slices]
            ids[m] = bids[slices][m]
            datas[m] = bdatas[slices][m]
        else:
            # Otherwise overwrite all blocks.
            ids[:] = bids[slices]
            datas[:] = bdatas[slices]



# Returns the neighbourhood box.
def get_neighbourhood(level, box, strength):
    # Need to expand the box to include `strength` extra blocks in all
    # directions, so that we can find the blocks in a `strength` radius around
    # every block in the actual selection. Aka, we don't need each house, we need
    # the whole neighbourhood. Also, if feathering we only need 1 additional
    # block in each direction.
    nbh = box.expand(strength)

    # We can just clamp the y axis instead of throwing if the selection grows too
    # tall. This clamping is dealt with in `smooth` when shifting, by assuming
    # that the closest layer is repeated out-of-bounds.
    x, _, z = nbh.origin
    w, _, l = nbh.size
    max_box = BoundingBox(origin=(x, 0, z), size=(w, 256, l))
    nbh = nbh.intersect(max_box)

    # However, must ensure that we don't go out of bounds of the world. So check
    # all the chunks the box touches actually exist. Check first, with a
    # different message, that the actual selection doesn't contain missing
    # chunks.
    if not br.chunks_exist(level, box):
        raise Exception("Selection cannot contain missing chunks.")
    if not br.chunks_exist(level, nbh):
        raise Exception("Selection is too close to missing chunks.")

    return nbh


# Returns a dictionary of blocks (as `bid, bdata`) to a `count_type` array of
# their locations in selection (where =0 does not match and =1 means matches).
def extract(level, nbh):
    blocks = {}

    # Go through all the unique blocks in the selection.
    for ids, datas, slices in br.iterate(level, nbh, br.BLOCKS):
        for block in br.unique_blocks(ids, datas):
            # If this is the first time this block showed up, we must assume it's
            # never showed up anyway and initialise to zeroes.
            if block not in blocks:
                blocks[block] = np.zeros(br.shape(nbh), dtype=count_type)

            # Update this block's mask.
            bid, bdata = block
            blocks[block][slices] = ((ids == bid) & (datas == bdata))

    return blocks


# Adds all neighbour influences to each block's array.
def smear(blocks, strength):
    # Allocate two arrays that are used for temporary memory.
    example_mask = blocks.values()[0]
    tmp1 = np.empty_like(example_mask)
    tmp2 = np.empty_like(example_mask)

    # Add in a cube for each block.
    for mask in blocks.values():
        sum_cube(mask, strength, tmp1, tmp2)


# Simple algorithm to in-place sum in a cube of radius `size` around each cell.
def sum_cube(array, size, tmp1, tmp2):
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


# Returns a tuple of `bids, bdatas`, where each block is the most common of the
# blocks at that location.
def most_common(blocks):
    # Get a 4d array of all block counts.
    all_blocks = np.stack(list(blocks.values()))

    # Find the index (into `blocks`) of the most common block (which will have
    # the maximum count).
    most_common_indices = np.argmax(all_blocks, axis=0)

    # Get a numpy vectorized function to convert the indices to the block id and
    # data.
    index = list(blocks.keys())
    lookup = np.vectorize(lambda i: index[i])

    # Return the thang. Note that this numpy vectorized function will return a
    # tuple of arrays (not an array of tuples, however that would work).
    return lookup(most_common_indices)
