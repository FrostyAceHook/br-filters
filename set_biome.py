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

    # Too easy?
    for biomes, _ in br.iterate(level, box, br.BIOMES):
        biomes[:] = biome

    print "Finished setting biomes."
    print "- biome: {}".format(br.biome_str(biome))
    return
