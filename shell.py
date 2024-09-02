import numpy as np
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


displayName = "Shell"


inputs = (
    ("Cheeky bedrock box filter. If used with a selection where one dimension "
            "is only 1 block long, it will make a ring.", "label"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Bedrock),
    br.selector_explain("replace"),
)


def perform(level, box, options):
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Get the block mask.
    shell = get_shell(box)

    # Place em (holey style).
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS, holey=True):
        mask = shell[slices]
        mask &= replace.matches(ids, datas)

        ids[mask] = bid
        datas[mask] = bdata


    print "Finished shelling."
    print "- replace: {}".format(replace)
    print "- block: ({}:{})".format(bid, bdata)
    return


def get_shell(box):
    if sum(d == 1 for d in box.size) > 1:
        raise Exception("Cannot have a selection with more than one dimension "
                "of length 1.")

    # Basic idea: create a smaller box inside the main one which to not include
    # positions from.

    # Shrink in every direction except for any with 1 length (may be none).
    shrinked_box = box.expand(*(-(d != 1) for d in box.size))
    # shrunk
    # shronk
    # shrenk
    # shrank

    # Mask every block.
    mask = np.ones(br.shape(box), dtype=bool)

    # Exclude the inner box.
    mask[br.submask(box, shrinked_box)] = False

    return mask
