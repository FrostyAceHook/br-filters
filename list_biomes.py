import br
import numpy as np
from collections import defaultdict

displayName = "List Biomes"

inputs = (
    ("Lists the biomes in the selection to the console.", "label"),
    ("Map?", False),
)


def perform(level, box, options):
    do_map = options["Map?"]

    # Get all occuring ids and how much they occur.
    totals = defaultdict(int)
    for biomes, _ in br.iterate(level, box, br.BIOMES):
        # Get the unique biomes and counts.
        biome_ids, counts = np.unique(biomes, return_counts=True)
        # Add them to totals.
        for biome, count in zip(biome_ids, counts):
            totals[biome] += count

    # Sort biomes from most-frequent to least.
    totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)


    # Print all the biome names and ids.
    print "{} biome{}:".format(len(totals), "" if len(totals) == 1 else "s")
    for biome, count in totals:
        print "  {}: {} columns".format(br.biome_str(biome), count)


    # Now do a sick map of the entire square selection.
    CHARSET = " .:~!?=+*#%$&@"

    # Aaaactually gotta check if we should (if there are few enough biomes to fit
    # in the limited charset but also not just one biome).

    if do_map and len(totals) == 1:
        print "No need for a sick map (mono-biomic)."
        do_map = False

    if do_map and len(totals) > len(CHARSET):
        print ("Too many biomes for a sick map (got {}, can be at-most {})."
                .format(len(totals), len(CHARSET)))
        do_map = False

    if do_map:
        print "But now for a sick map:"

        # Assign the most-frequent biomes the earliest indices (aka make them
        # darker characters and stand-out less).
        charmap = dict()
        for i, (biome, _) in enumerate(totals):
            # https://www.desmos.com/calculator/frji73r84b
            index = int(round(float(i) / (len(totals) - 1) * (len(CHARSET) - 1)))
            charmap[biome] = CHARSET[index]

        # Get an array of all the biomes.
        shape = br.shape(box)[:2] # xz shape.
        all_biomes = np.empty(shape, dtype=np.uint8)
        for biomes, slices in br.iterate(level, box, br.BIOMES):
            all_biomes[slices] = biomes

        # PRINT THE MAAP

        # example:
        #
        #   North
        #     ^
        #
        # z = -10
        #    ,------------------,
        #    |                  |
        #    |   ####           |
        #    |    @@@           |
        #    |                  |
        #    '------------------'
        # z = 10
        #  x = -10            x = 10
        #
        # Index:
        #  ' ' = "Forest" (4)
        #  '#' = "Ocean" (0)
        #  '@' = "Desert" (2)
        #

        print ""
        print "  North"
        print "    ^ "
        print ""
        print "z = {}".format(box.minz)

        print "   ,{},".format("-" * box.width)
        for row in all_biomes.T:
            print "   |{}|".format("".join(charmap[x] for x in row))
        print "   '{}'".format("-" * box.width)

        print "z = {}".format(box.maxz - 1)
        print " x = {0} {2}x = {1}".format(box.minx, box.maxx - 1,
                " " * (box.width - 4 - len(str(box.minx))))
        print ""

        print "Index:"
        for biome, _ in totals:
            print " '{}' = {}".format(charmap[biome], br.biome_str(biome))


    print "Finished listing biomes."
    return
