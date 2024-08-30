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


displayName = "Gridify 4"
# FOUR


inputs = (
    ("issa grid innit. Swap blocks is a purely convenience option, which acts "
            "as-if 'block 2' had been selected for 'block 1', and vice versa.",
            "label"),
    ("Replace:", "string"),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 2:", alphaMaterials.Cobblestone),
    ("Swap blocks?", False),
    br.selector_explain("replace"),
)


def perform(level, box, options):
    # Get some options.
    replace = br.selector("replace", options["Replace:"])
    bid1, bdata1 = options["Block 1:"].ID, options["Block 1:"].blockData
    bid2, bdata2 = options["Block 2:"].ID, options["Block 2:"].blockData
    swap = int(options["Swap blocks?"])

    # Make true/false alternating in a grid the size of the selection.
    w, l, h = br.shape(box)
    odd = (np.arange(w)[:, None, None] + np.arange(l)[:, None] + np.arange(h) +
            swap) % 2 # cheekily incorperate the swap option.

    # Do the thang. Note this filter is holey, because missing chunks can just be
    # skipped without consequence.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS, holey=True):
        # Get the block matches (she was a moth to the flame type shit).
        mask = replace.matches(ids, datas)

        # Get the current slice of the odd array.
        cur_odd = odd[slices]

        # Set each block type.

        mask1 = (mask & (cur_odd == 0))
        ids[mask1] = bid1
        datas[mask1] = bdata1

        mask2 = (mask & (cur_odd == 1))
        ids[mask2] = bid2
        datas[mask2] = bdata2


    print "Finished gridifying."
    print "- replace: {}".format(replace)
    print "- block 1: ({}:{})".format(bid1, bdata1)
    print "- block 2: ({}:{})".format(bid2, bdata2)
    print "- swap blocks: {}".format(bool(swap))
    # you ever just wanna eat a shoe.
    # i eat sneakers.
    return
    # delicious
