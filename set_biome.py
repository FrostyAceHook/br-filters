import br

displayName = "Set Biome"

inputs = (
    ("Sets the biome of the selection. Note that biomes affect an entire column "
            "of blocks in this verison. Also note that these biomes do not "
            "exist for every version, be sure to check that is does before "
            "using.", "label"),
    ("Biome:", br.BIOME_NAMES),
)


def perform(level, box, options):
    # Get the biome id.
    biome = br.BIOME_IDOF[options["Biome:"]]

    print "Biome: {}".format(br.biome_str(biome))

    # Too easy?
    for biomes, _ in br.iterate(level, box, br.BIOMES):
        biomes[:] = biome

    print "Finished setting biomes."
    return
