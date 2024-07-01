import br
import numpy as np
from pymclevel import alphaMaterials, BoundingBox

displayName = "Shell"

inputs = (
    ("Block:", alphaMaterials.Bedrock),
    ("Cheeky bedrock box filter. If used with a selection where one dimension "
            "is only 1 block long, it will make a ring.", "label"),
)


def perform(level, box, options):
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Get the block mask.
    mask = get_mask(box)

    # Place em (holey style).
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS, holey=True):
        cur_mask = mask[slices]

        ids[cur_mask] = bid
        datas[cur_mask] = bdata


    print "Finished shelling."
    return


def get_mask(box):
    if sum(d == 1 for d in box.size) > 1:
        raise Exception("Cannot have a selection with more than one dimension "
                "of length 1.")

    # Basic idea: create a smaller box inside the main one which to not include
    # positions from.

    # Shrink in every direction except for any with 1 length (may be none).
    shrinked_box = BoundingBox(size=box.size) # relative to 0,0,0.
    shrinked_box = shrinked_box.expand(*(-(d != 1) for d in box.size))
    # shrunk
    # shronk
    # shrenk
    # shrank

    # Mask every block.
    mask = np.ones(br.shape(box), dtype=bool)

    # Exclude the inner box.
    mask[br.box_slices(shrinked_box)] = 0

    return mask
