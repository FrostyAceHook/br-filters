import br
import numpy as np
from pymclevel import alphaMaterials

displayName = "Varied"

inputs = (
    ("Replace except?", True),
    ("Replace 1:", alphaMaterials.Air),
    ("Replace 1?", True),
    ("Replace 2:", alphaMaterials.Air),
    ("Replace 2?", False),
    ("Replace 3:", alphaMaterials.Air),
    ("Replace 3?", False),
    ("Replace 4:", alphaMaterials.Air),
    ("Replace 4?", False),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 1 weight:", (1, 0, 32767)),
    ("Block 2:", "blocktype"),
    ("Block 2 weight:", (0, 0, 32767)),
    ("Block 3:", "blocktype"),
    ("Block 3 weight:", (0, 0, 32767)),
    ("Block 4:", "blocktype"),
    ("Block 4 weight:", (0, 0, 32767)),
    ("Replaces the \"replace\" blocks with a random block from the above four, "
            "each with a weighted proportion. If block id 256 is used and be "
            "placed, the block is left unchanged instead.")
)



def perform(level, box, options):
    replace = br.from_options(options, "Replace", count=4)
    place = br.from_options(options, "Block", count=4)

    block_weights = [options["Block {} weight:".format(i)] for i in (1,2,3,4)]
    # Check at least one weight is non-zero.
    if sum(block_weights) == 0:
        raise Exception("Cannot have all zero weights champ.")

    # Get the cumulative and scaled weights to categorise random numbers.
    block_cumweights = np.cumsum(block_weights) / float(sum(block_weights))


    # Iterate through the chunks, find the blocks to replace, get the proportions
    # and set them blocks. This can be holey cause skipping any missing chunks is
    # okie dokie.
    for ids, datas in br.iterate(level, box, holey=True):
        # Get the replacement mask.
        mask = replace.matches(ids, datas)

        # Get a random value for each block to replace.
        block_randoms = np.random.random(mask.shape)

        # Use digitize to convert each value to a block index.
        block_indices = np.digitize(block_randoms, block_cumweights)

        # Convert the block indices to the actual ids/datas.
        for i, (bid, bdata) in enumerate(place):
            # Find the blocks of this index, only replacing the "replace" blocks.
            cur_mask = (mask & (block_indices == i))

            # id 256 means skip block.
            if bid == 256:
                continue

            # Set the blocks of this type.
            ids[cur_mask] = bid
            datas[cur_mask] = bdata


    print "Finished varying."
    return
