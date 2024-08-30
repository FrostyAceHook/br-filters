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


displayName = "Find empty chests"


inputs = (
    ("Prints the locations of any empty chests to the console.", "label"),
)


def perform(level, box, options):
    # Store all coordinates of empty chests.
    positions = []

    print "Finding empty chests:"

    # Iterate the tile entities.
    for teid, pos, te in br.iterate(level, box, br.TES):
        # Check it's a chest. First value is for pre 1.11, others for post.
        if teid not in {"Chest", "chest", "minecraft:chest"}:
            continue

        # Add it if it's empty.
        if not te["Items"]:
            positions.append(pos)

    # Print the findings.
    count = len(positions)
    if count:
        print "- found {} empty chest{}, at:".format(count, br.plural(count))
        for pos in positions:
            print "- {}".format(pos)
    else:
        print "- found no empty chests."

    return
