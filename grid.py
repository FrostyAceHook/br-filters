import br
import numpy as np
from pymclevel import alphaMaterials

displayName = "Gridify 4"
# FOUR


inputs = (
    ("NOTE: Uses a selector string for 'replace'.\n"
            "See `br.py` for the selector string syntax specifics. For simple "
            "use, just type a block id/name with optional data (i.e. \"stone\" "
            "for any stone or \"stone:3\" for diorite).", "label"),
    ("Replace:", "string"),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 2:", alphaMaterials.Cobblestone),
    ("Swap blocks?", False),
    ("issa grid innit. Swap blocks is a purely convenience option.", "label"),
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
    for ids, datas, slices in br.iterate(level, box, br.SLICES, holey=True):
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
    # you ever just wanna eat a shoe.
    # i eat sneakers.
    return
    # delicious
