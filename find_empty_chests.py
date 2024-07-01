import br
from pymclevel import TileEntity

displayName = "Find empty chests"

inputs = (
    ("Gaming?", True), # does ntohing lmoa.
    ("Check the console for the results.", "label"),
)


def perform(level, box, options):
    # Store all coordinates of empty chests.
    positions = []

    # Iterate the tile entities.
    for teid, pos, te in br.iterate(level, box, br.TES):
        # Check it's a chest. First value is for pre 1.11, second for post.
        if teid not in {"Chest", "minecraft:chest"}:
            continue

        # Add it if it's empty.
        if len(te["Items"]) == 0:
            poses.append(pos)

    # Print the findings.
    count = len(positions)
    print "Found {} empty chest{}.".format(count, "s" if (count != 1) else "")
    for pos in positions:
        print pos

    return
