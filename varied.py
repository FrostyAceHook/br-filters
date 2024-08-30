import numpy as np
from pymclevel import alphaMaterials

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you put it in the same "
            "filter folder? It can be downloaded from: "
            "github.com/FrostyAceHook/br-filters")
try:
    br.require_version(2, 1)
except AttributeError:
    raise ImportError("Outdated version of 'br.py'. Please download the latest "
            "compatible version from: github.com/FrostyAceHook/br-filters")


displayName = "Varied"


inputs = (
    ("Replaces the 'replace' blocks with a random block from the above four, "
            "each with a weighted proportion. If block id 256 is used as a "
            "block, anywhere it would be placed is left unchanged instead.",
            "label"),
    ("Replace:", "string"),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 1 weight:", (1.0, 0.0, 1000.0)),
    ("Block 2:", alphaMaterials.Air),
    ("Block 2 weight:", (0.0, 0.0, 1000.0)),
    ("Block 3:", alphaMaterials.Air),
    ("Block 3 weight:", (0.0, 0.0, 1000.0)),
    ("Block 4:", alphaMaterials.Air),
    ("Block 4 weight:", (0.0, 0.0, 1000.0)),
    br.selector_explain("replace"),
)


def perform(level, box, options):
    replace = br.selector("replace", options["Replace:"])

    blocks = [options["Block {}:".format(i)] for i in (1,2,3,4)]
    blocks = [(block.ID, block.blockData) for block in blocks]

    block_weights = [options["Block {} weight:".format(i)] for i in (1,2,3,4)]
    # Check at least one weight is non-zero.
    if sum(block_weights) == 0.0:
        raise Exception("Cannot have all zero weights champ.")

    # Get the cumulative and scaled weights to categorise random numbers.
    block_cumweights = np.cumsum(block_weights) / sum(block_weights)


    # Iterate through the chunks, find the blocks to replace, get the proportions
    # and set them blocks. This can be holey cause skipping any missing chunks is
    # okie dokie.
    for ids, datas, _ in br.iterate(level, box, br.BLOCKS, holey=True):
        # Get the replacement mask.
        mask = replace.matches(ids, datas)

        # Get a random value for each block to replace.
        block_randoms = np.random.random(mask.shape)

        # Use digitize to convert each value to a block index.
        block_indices = np.digitize(block_randoms, block_cumweights)

        # Convert the block indices to the actual ids/datas.
        for i, (bid, bdata) in enumerate(blocks):
            # Find the blocks of this index, only replacing the "replace" blocks.
            cur_mask = (mask & (block_indices == i))

            # id 256 means skip block.
            if bid == 256:
                continue

            # Set the blocks of this type.
            ids[cur_mask] = bid
            datas[cur_mask] = bdata


    print "Finished varying."
    print "- replace: {}".format(replace)
    for i, ((bid, bdata), bweight) in enumerate(zip(blocks, block_weights)):
        if bweight == 0.0:
            continue
        if bid != 256:
            print "- block {}: ({}:{})".format(i + 1, bid, bdata)
        else:
            print "- block {}: unchanged".format(i + 1)
        print "- block {} weight: {}".format(i + 1, bweight)
    return
