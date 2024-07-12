import br
import numpy as np
from collections import OrderedDict
from copy import deepcopy
from pymclevel import TAG_Byte, TAG_Short, TAG_Int, TAG_String, TAG_List, \
        TAG_Compound, TileEntity
from random import randint

displayName = "Spawner Manip"


# Note that 1.12 entity ids are a superset of 1.8 not only for new mobs. Mobs
# such as wither skeletons use entity id "Skeleton" in 1.8 and entity data to
# distinguish them, whereas 1.12 has a separate id for them.

# Map from 1.12 ids to 1.8 ids.
#  [0] = 1.8 entity id.
#  [1] = optional, dictionary of extra entity data needed in 1.8.
EIDS_1_12_TO_1_8 = {
    # "minecraft:area_effect_cloud": no equivalent.
    "minecraft:armor_stand": ("ArmorStand", ),
    "minecraft:arrow": ("Arrow", ),
    "minecraft:bat": ("Bat", ),
    "minecraft:blaze": ("Blaze", ),
    "minecraft:boat": ("Boat", ),
    "minecraft:cave_spider": ("CaveSpider", ),
    "minecraft:chest_minecart": ("MinecartChest", ),
    "minecraft:chicken": ("Chicken", ),
    "minecraft:commandblock_minecart": ("MinecartCommandBlock", ),
    "minecraft:cow": ("Cow", ),
    "minecraft:creeper": ("Creeper", ),
    "minecraft:donkey": ("EntityHorse", {"Type": TAG_Int(1)}),
    # "minecraft:dragon_fireball": no equivalent.
    "minecraft:egg": ("ThrownEgg", ),
    "minecraft:elder_guardian": ("ElderGuardian", ),
    "minecraft:ender_crystal": ("EnderCrystal", ),
    "minecraft:ender_dragon": ("EnderDragon", ),
    "minecraft:ender_pearl": ("ThrownEnderpearl", ),
    "minecraft:enderman": ("Enderman", ),
    "minecraft:endermite": ("Endermite", ),
    # "minecraft:evocation_fangs": no equivalent.
    # "minecraft:evocation_illager": no equivalent.
    "minecraft:eye_of_ender_signal": ("EyeOfEnderSignal", ),
    "minecraft:falling_block": ("FallingSand", ),
    "minecraft:fireball": ("Fireball", ),
    "minecraft:fireworks_rocket": ("FireworksRocketEntity", ),
    "minecraft:furnace_minecart": ("MinecartFurnace", ),
    "minecraft:ghast": ("Ghast", ),
    "minecraft:giant": ("Giant", ),
    "minecraft:guardian": ("Guardian", ),
    "minecraft:hopper_minecart": ("MinecartHopper", ),
    "minecraft:horse": ("EntityHorse", ),
    # "minecraft:husk": no equivalent.
    # "minecraft:illusion_illager": no equivalent.
    "minecraft:item": ("Item", ),
    "minecraft:item_frame": ("ItemFrame", ),
    "minecraft:leash_knot": ("LeashKnot", ),
    "minecraft:lightning_bolt": ("LightningBolt", ),
    # "minecraft:llama": no equivalent.
    # "minecraft:llama_spit": no equivalent.
    "minecraft:magma_cube": ("LavaSlime", ),
    "minecraft:minecart": ("MinecartRideable", ),
    "minecraft:mooshroom": ("MushroomCow", ),
    "minecraft:mule": ("EntityHorse", {"Type": TAG_Int(2)}),
    "minecraft:ocelot": ("Ozelot", ),
    "minecraft:painting": ("Painting", ),
    # "minecraft:parrot": no equivalent.
    "minecraft:pig": ("Pig", ),
    # "minecraft:polar_bear": no equivalent.
    "minecraft:potion": ("ThrownPotion", ),
    "minecraft:rabbit": ("Rabbit", ),
    "minecraft:sheep": ("Sheep", ),
    # "minecraft:shulker": no equivalent.
    # "minecraft:shulker_bullet": no equivalent.
    "minecraft:silverfish": ("Silverfish", ),
    "minecraft:skeleton": ("Skeleton", ),
    "minecraft:skeleton_horse": ("EntityHorse", {"Type": TAG_Int(4)}),
    "minecraft:slime": ("Slime", ),
    "minecraft:small_fireball": ("SmallFireball", ),
    "minecraft:snowball": ("Snowball", ),
    "minecraft:snowman": ("SnowMan", ),
    "minecraft:spawner_minecart": ("MinecartSpawner", ),
    # "minecraft:spectral_arrow": no equivalent.
    "minecraft:spider": ("Spider", ),
    "minecraft:squid": ("Squid", ),
    # "minecraft:stray": no equivalent.
    "minecraft:tnt": ("PrimedTnt", ),
    "minecraft:tnt_minecart": ("MinecartTNT", ),
    # "minecraft:vex": no equivalent.
    "minecraft:villager": ("Villager", ),
    "minecraft:villager_golem": ("VillagerGolem", ),
    # "minecraft:vindication_illager": no equivalent.
    "minecraft:witch": ("Witch", ),
    "minecraft:wither": ("WitherBoss", ),
    "minecraft:wither_skeleton": ("Skeleton", {"SkeletonType": TAG_Byte(1)}),
    "minecraft:wither_skull": ("WitherSkull", ),
    "minecraft:wolf": ("Wolf", ),
    "minecraft:xp_bottle": ("ThrownExpBottle", ),
    "minecraft:xp_orb": ("XPOrb", ),
    "minecraft:zombie": ("Zombie", ),
    "minecraft:zombie_horse": ("EntityHorse", {"Type": TAG_Int(3)}),
    "minecraft:zombie_pigman": ("PigZombie", ),
    "minecraft:zombie_villager": ("Zombie", {"IsVillager": TAG_Byte(1)}),
}


# Curated and ordered list of entites to display, since the others are either
# rarely used, or only useful with custom spawn data and therefore out of scope
# of this filter. Note this maps to the 1.12 entity id, since they are all
# unique.
EIDS = OrderedDict([
    ("unchanged",       None),
    ("zombie",          "minecraft:zombie"),
    ("skeleton",        "minecraft:skeleton"),
    ("creeper",         "minecraft:creeper"),
    ("spider",          "minecraft:spider"),
    ("cave spider",     "minecraft:cave_spider"),
    ("blaze",           "minecraft:blaze"),
    ("wither skeleton", "minecraft:wither_skeleton"),
    ("ghast",           "minecraft:ghast"),
    ("husk (1.12 only)", "minecraft:husk"),
    ("stray (1.12 only)", "minecraft:stray"),
    ("slime",           "minecraft:slime"),
    ("magma cube",      "minecraft:magma_cube"),
    ("witch",           "minecraft:witch"),
    ("silverfish",      "minecraft:silverfish"),
    ("endermite",       "minecraft:endermite"),
    ("enderman",        "minecraft:enderman"),
    ("guardian",        "minecraft:guardian"),
    ("elder guardian",  "minecraft:elder_guardian"),
    ("giant",           "minecraft:giant"),
    ("iron golem",      "minecraft:villager_golem"),
    ("snowman",         "minecraft:snowman"),
    ("bat",             "minecraft:bat"),
    ("cow",             "minecraft:cow"),
    ("mooshroom",       "minecraft:mooshroom"),
    ("pig",             "minecraft:pig"),
    ("sheep",           "minecraft:sheep"),
    ("chicken",         "minecraft:chicken"),
    ("rabbit",          "minecraft:rabbit"),
    ("squid",           "minecraft:squid"),
    ("wolf",            "minecraft:wolf"),
    ("ocelot",          "minecraft:ocelot"),
    ("horse",           "minecraft:horse"),
    ("donkey",          "minecraft:donkey"),
    ("mule",            "minecraft:mule"),
    ("zombie horse",    "minecraft:zombie_horse"),
    ("skeleton horse",  "minecraft:skeleton_horse"),
    ("villager",        "minecraft:villager"),
])


# Valid tile entity ids for spawners.
SPAWNER_TEID = {"MobSpawner", "mob_spawner", "minecraft:mob_spawner"}


# A TAG_Short property option. -1 indicates leave unchanged.
PROPERTY = (-1, -1, 32767)

inputs = [
    (
        ("Set", "title"),
        ("Modifies and validates all spawners. Note this attempts to preserve "
                "all the spawner data, however it is possible for it to corrupt "
                "them sooo make a backup :)."
                "\nUse \"-1\" (or \"unchanged\" for 'entity') to leave a "
                "property unchanged.", "label"),
        ("Version:", ("1.12", "1.8")),
        ("Entity:", tuple(EIDS.keys())),
        ("Spawn count:", PROPERTY),
        ("Spawn range:", PROPERTY),
        ("Min delay:", PROPERTY),
        ("Max delay:", PROPERTY),
        ("Required player range:", PROPERTY),
        ("Max nearby entities:", PROPERTY),
        ("Min initial delay:", PROPERTY),
        ("Max initial delay:", PROPERTY),
        ("Note that 'min delay' and 'max delay' are spawner properties which "
                "dictate the timing range between successive spawns, whereas "
                "with 'initial delay' the filter picks a random number within "
                "the given range (inclusive) and sets the current time-until-"
                "next-spawn to that. Both are in ticks.", "label"),
    ),

    (
        ("Create", "title"),
        ("Replaces the blocks with default spawners.", "label"),
        ("NOTE: Uses a selector string for 'replace'.\n"
                "See `br.py` for the selector string syntax specifics. For "
                "simple use, just type a block id/name with optional data (i.e. "
                "\"stone\" for any stone or \"stone:3\" for diorite).", "label"),
        ("Replace:", "string"),
        (" Version:", ("1.12", "1.8")), # space to make unique.
    ),

    (
        ("Find", "title"),
        ("Find spawners with the given entity id and displays their coordinates "
                "in the console. Intended to be used to ensure there aren't "
                "unset pig spawners or similar.","label"),
        ("  Version:", ("1.12", "1.8")), # double space to make unique.
        ("Entity id:", "string"),
        ("Note for 1.12 'entity id' will be automatically prefixed with "
                "\"minecraft:\" if needed.", "label"),
    ),

    (
        ("List", "title"),
        ("Lists the nbt of all spawners in the console.", "label"),
    ),
]


def perform(level, box, options):
    # Get the operation to perform based on which page is open.
    op = (
        op_set,
        op_create,
        op_find,
        op_list,
    )[options["__page_index__"]]

    # Invoke the thang.
    op(level, box, options)

    # Give a nice message.
    # print "Have a good day :D"
    # just kidding.
    return


# Is `comp[key]` of type `t`?
def has(comp, key, t):
    if comp is None:
        return False
    if key not in comp:
        return False
    return isinstance(comp[key], t)


# Returns a TAG_Compound of a valid spawner tile entity, deriving as much
# information as possible from `old_spawner` (except position). If `set_entity`
# is not None, the entity id will be set to it (note it's fine to universally use
# a 1.12 id for this, it will be version validated after setting).
def gen_spawner(version, pos, old_spawner=None, set_entity=None):
    if version not in {"1.12", "1.8"}:
        raise Exception("how has this happened")

    # Create the basic stuff like id and pos.
    spawner = TAG_Compound()
    TileEntity.setpos(spawner, pos)
    if version == "1.8":
        spawner["id"] = TAG_String(u"MobSpawner")
    elif version == "1.12":
        spawner["id"] = TAG_String(u"minecraft:mob_spawner")



    # Set attributes to the default spawner values (as-if you placed one in-
    # game). Note these are named the same for 1.8 and 1.12.
    def set_attr(key, t, dflt):
        if has(old_spawner, key, t):
            spawner[key] = deepcopy(old_spawner[key])
        else:
            spawner[key] = t(dflt)

    set_attr("SpawnCount", TAG_Short, 4)
    set_attr("SpawnRange", TAG_Short, 4)
    set_attr("MinSpawnDelay", TAG_Short, 200)
    set_attr("MaxSpawnDelay", TAG_Short, 800)
    set_attr("RequiredPlayerRange", TAG_Short, 16)
    set_attr("MaxNearbyEntities", TAG_Short, 6)
    set_attr("Delay", TAG_Short, 0)



    # Entity data is different from 1.8 to 1.12, but they both have the same
    # general idea of:
    # - one "primary" mob (i think the one that's going to spawn next, this is
    #       the one that's displayed in the spawner)
    # - several (or none) "potential" mobs (i think these are selected from after
    #       the spawner spawns a primary mob to determine the next primary mob).
    # The specific format for each version is:
    # 1.8:
    # - primary:
    #   - entity id in "EntityId" TAG_String.
    #   - entity data in "SpawnData" TAG_Compound (which doesn't have an "id"
    #       tag).
    # - potential:
    #   - stored in the "SpawnPotentials" TAG_List.
    #   - Each element is:
    #       - "Weight" TAG_Int of the relative probability of this entity.
    #       - "Type" TAG_String of the entity id.
    #       - "Properties" TAG_Compound of the entity data (which again doesn't
    #           have an "id" tag).
    # 1.12:
    # - primary:
    #   - entity id in "SpawnData"."id" TAG_String.
    #   - entity data in "SpawnData" TAG_Compound minus "id" tag.
    # - potential:
    #   - stored in the "SpawnPotentials" TAG_List.
    #   - Each element is:
    #       - "Weight" TAG_Int of the relative probability of this entity.
    #       - "Entity" TAG_Compound of the same form as "SpawnData".
    #
    # 1.8 fails to create a valid spawner without a primary.
    # 1.12, the fucking goat, back-fills the primary from the potentials if
    # missing.
    #
    # Both versions are able to forward-fill the potentials from the primary if
    # the potentials are missing.

    class Entity:
        def __init__(self, eid=None, edata=TAG_Compound(), weight=1):
            self.eid = eid          # unicode.
            self.edata = edata      # TAG_Compound.
            self.weight = weight    # int.
            # All attributes are references and should be deepcopied into the new
            # spawner.

        def finalise(self, version):
            assert self.eid is not None

            if version == "1.8":
                # Convert from 1.12 eid to 1.8 if we recognise it.
                if self.eid in EIDS_1_12_TO_1_8:
                    lookup = EIDS_1_12_TO_1_8[self.eid]

                    self.eid = lookup[0]
                    # Some ids in 1.12 dont map directly to a 1.8 and have
                    # additional data which we gotta add.
                    if len(lookup) > 1:
                        # Copy to not modify other references.
                        self.edata = deepcopy(self.edata)
                        for k, v in lookup[1].items():
                            self.edata[k] = v

                # Wipe the "id" tag in edata if it's present.
                if has(self.edata, "id", TAG_String):
                    del self.edata["id"]

            elif version == "1.12":
                # Annoying to convert forwards, gotta check that the entity data
                # matches and then wipe it.
                for eid_1_12, lookup in EIDS_1_12_TO_1_8.items():
                    # Check if the name matches.
                    eid_1_8 = lookup[0]
                    if self.eid != eid_1_8:
                        continue
                    # Check if the additional data matches.
                    if len(lookup) > 1:
                        all_match = True
                        for k, v in lookup[1].items():
                            if k not in self.edata:
                                all_match = False
                            elif self.edata[k].value != v.value:
                                all_match = False
                        if not all_match:
                            continue

                    # Ok now we can update the eid to the 1.12 and wipe the no-
                    # longer needed edata.
                    self.eid = eid_1_12
                    if len(lookup) > 1:
                        # Copy to not modify other references.
                        self.edata = deepcopy(self.edata)
                        for k in lookup[1]:
                            del self.edata[k]


    primary = Entity()
    potentials = []


    # Parse the mobs from the old spawner if they aren't going to be overridden.
    if set_entity is None:

        # Both versions store edata in "SpawnData", but in 1.12 this also has an
        # "id" tag.
        if has(old_spawner, "SpawnData", TAG_Compound):
            primary.edata = old_spawner["SpawnData"]

        # Check for 1.8 id.
        if has(old_spawner, "EntityId", TAG_String):
            primary.eid = old_spawner["EntityId"].value
        # Otherwise try grab the eid from the spawn data (i.e. 1.12 format).
        elif has(primary.edata, "id", TAG_String):
            primary.eid = primary.edata["id"].value

        # Note `primary.eid` may still be None here if there is no primary mob.


        # Parse the potential mobs.

        if has(old_spawner, "SpawnPotentials", TAG_List):
            for potential in old_spawner["SpawnPotentials"]:
                if not isinstance(potential, TAG_Compound):
                    continue
                entity = Entity()

                if has(potential, "Weight", TAG_Int):
                    entity.weight = potential["Weight"].value
                # Otherwise leave as default (1).

                # Try both entity data locations, with a preference for 1.12
                # format.
                if has(potential, "Entity", TAG_Compound):
                    entity.edata = potential["Entity"]
                elif has(potential, "Properties", TAG_Compound):
                    entity.edata = potential["Properties"]

                # Check for 1.8 id.
                if has(potential, "Type", TAG_String):
                    entity.eid = potential["Type"].value
                # Otherwise try back-fill from edata (i.e. 1.12 format).
                elif has(entity.edata, "id", TAG_String):
                    entity.eid = entity.edata["id"].value


                # Add it if it parsed a valid entity.
                if entity.eid is not None:
                    potentials.append(entity)


        # Do back-fill by grabbing primary from first potential.
        if primary.eid is None and potentials:
            primary = potentials[0]


        # Cheeky insert a default primary of pig.
        if primary.eid is None:
            if version == "1.8":
                primary = Entity(eid=u"Pig")
            elif version == "1.12":
                primary = Entity(eid=u"minecraft:pig")


    # Otherwise use the given mob.
    else:
        # Just chuck the mob id in there. It'll be fixed up in `finalise`.
        primary = Entity(eid=set_entity)



    # Do forward-fill by setting as a single potential of the primary.
    if not potentials:
        assert primary.weight == 1
        potentials.append(primary)


    # Validate all the entities. This may do version conversion (mad name innit).
    primary.finalise(version)
    for entity in potentials:
        entity.finalise(version)



    # Now setup the new spawner.


    # Set primary.

    if version == "1.8":
        spawner["EntityId"] = TAG_String(primary.eid)
        if primary.edata:
            spawner["SpawnData"] = deepcopy(primary.edata)
        # Note "SpawnData" is optional in 1.8.

    elif version == "1.12":
        # Do SpawnData first, also note it's mandatory (it stores the eid).
        if primary.edata:
            spawner["SpawnData"] = deepcopy(primary.edata)
        else:
            spawner["SpawnData"] = TAG_Compound()

        # Set the "id" (overwriting it if it's already there, who cares it should
        # be the same value anyway).
        spawner["SpawnData"]["id"] = TAG_String(primary.eid)


    # Set potentials.

    # Note: weird qwerk of 1.8 is that spawn potentials are only required or even
    # auto-generated by the game if the primary has custom spawn data. So, check
    # if potentials are even necessary and otherwise leave it out.
    no_need = (
        (version == "1.8") and
        (not primary.edata) and
        (len(potentials) == 1) and
        (potentials[0].eid == primary.eid) and
        (not potentials[0].edata)
    )
    # If no need, we done early :).
    if no_need:
        return spawner


    # Otherwise we gotta fill in the potentials :(.
    spawner["SpawnPotentials"] = TAG_List()
    for entity in potentials:
        potential = TAG_Compound()
        potential["Weight"] = TAG_Int(entity.weight)

        if version == "1.8":
            potential["Type"] = TAG_String(entity.eid)
            # Note "Properties" is not(?) optional in 1.8. it will get generated
            # otherwise i think but still, might as well set it to empty compound
            # if thats the case.
            potential["Properties"] = deepcopy(entity.edata)

        elif version == "1.12":
            # Same as w SpawnData, everything is in Entity.
            potential["Entity"] = deepcopy(entity.edata)

            # Set the "id", potentially overwriting.
            potential["Entity"]["id"] = TAG_String(entity.eid)

        spawner["SpawnPotentials"].append(potential)

    return spawner




def op_set(level, box, options):
    # Grab the args.
    version = options["Version:"]
    entity = options["Entity:"]
    spawn_count = options["Spawn count:"]
    spawn_range = options["Spawn range:"]
    required_player_range = options["Required player range:"]
    max_nearby_entities = options["Max nearby entities:"]
    min_delay = options["Min delay:"]
    max_delay = options["Max delay:"]
    min_initial_delay = options["Min initial delay:"]
    max_initial_delay = options["Max initial delay:"]


    # Check some args are valid.

    if entity.endswith("(1.12 only)") and version != "1.12":
        raise Exception("Cannot use a 1.12 entity in not-1.12.")

    if (min_delay == -1) != (max_delay == -1):
        raise Exception("Must set both 'min delay' and 'max delay' or neither.")

    if (min_initial_delay == -1) != (max_initial_delay == -1):
        raise Exception("Must set both 'min initial delay' and 'max initial "
                "delay' or neither.")

    if max_delay < min_delay:
        raise Exception("'max delay' cannot be smaller than 'min delay'")

    if max_initial_delay < min_initial_delay:
        raise Exception("'max initial delay' cannot be smaller than 'min "
                "initial delay'")


    # Tag name to the tag value of properties of the spawner. Doesn't include the
    # entity id or the initial delay.
    properties = {
        "SpawnCount": spawn_count,
        "SpawnRange": spawn_range,
        "MinSpawnDelay": min_delay,
        "MaxSpawnDelay": max_delay,
        "RequiredPlayerRange": required_player_range,
        "MaxNearbyEntities": max_nearby_entities,
    }


    # Iterate through all chunks in the selection.
    count = 0
    for chunk, _, _ in br.iterate(level, box, br.DEFAULT):
        tes = chunk.TileEntities
        # Iterate through all tile entities.
        for i, te in enumerate(tes):
            # Disregard oob or non-spawners.
            pos = TileEntity.pos(te)
            teid = te["id"].value
            if pos not in box or teid not in SPAWNER_TEID:
                continue


            # Get/validate the spawner nbt, setting the entity id here. Note if
            # the eid is "unchanged", `EIDS["unchanged"]` is none so it won't be
            # used.
            assert EIDS["unchanged"] is None
            spawner = gen_spawner(version, pos, te, set_entity=EIDS[entity])

            # Set delay.
            if min_initial_delay != -1:
                delay = randint(min_initial_delay, max_initial_delay)
                spawner["Delay"] = TAG_Short(delay)

            # Set the other properties.
            for key, value in properties.items():
                if value == -1: # leave unchanged.
                    continue

                # Everything else lines up w `key` and is short (lmao).
                spawner[key] = TAG_Short(value)

            # Replace the spawner.
            count += 1
            tes[i] = spawner


    print "Modified {} spawner{}.".format(count, "" if count == 1 else "s")
    return



def op_create(level, box, options):
    version = options[" Version:"] # note space.
    replace = br.selector("replace", options["Replace:"])

    # Kinda awkward spot we in because we need access to a chunk tile entities
    # for modification and blocks in selection. So, just make a joint lookup in
    # two separate passes.

    all_ids = []
    all_datas = []
    all_slices = []
    all_tes = []

    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        all_ids.append(ids)
        all_datas.append(datas)
        all_slices.append(slices)

    for chunk, _, _ in br.iterate(level, box, br.DEFAULT):
        all_tes.append(chunk.TileEntities)


    # Now we can iterate through the data in each chunk.
    count = 0
    for ids, datas, slices, tes in zip(all_ids, all_datas, all_slices, all_tes):
        # Get the mask of the replace blocks.
        mask = replace.matches(ids, datas)

        # Replace those blocks with spawner.
        ids[mask] = 52 # spawner id.
        datas[mask] = 0

        # Now handle the tile entity, namely destroying any previous and adding
        # the new one.

        # Get the coordinate of the bottom point in this section of the
        # selection.
        offset = np.array(box.origin)
        offset[0] += slices[0].start # x
        offset[1] += slices[2].start # y
        offset[2] += slices[1].start # z

        # Iter through the matching points and handle the tile entity.
        for pos in zip(*np.nonzero(mask)):
            # `pos` is in xzy order, we want xyz.
            pos = (pos[0], pos[2], pos[1])
            # The `pos` is relative to this section, so make it absolute.
            pos = [p + o for p, o in zip(pos, offset)]

            # Wipe any existing tile entity as this location. Annoying iterating
            # over a thing we're deleting.
            i = 0
            while i < len(tes):
                # are you fucking kidding me took me so long to realise that
                # [1,2,3] != (1,2,3) why would python do this to me. anyway `pos`
                # is now a list regardless.
                if TileEntity.pos(tes[i]) == pos:
                    del tes[i]
                else:
                    i += 1

            # Add the new tile entity.
            tes.append(gen_spawner(version, pos))

            # Cheeky telemetry (im beaming all your brainwaves straight to my
            # computer).
            count += 1


    print "Created {} spawner{}.".format(count, "" if count == 1 else "s")
    return



def op_find(level, box, options):
    version = options["  Version:"] # note two spaces.
    entity_id = options["Entity id:"]

    # If in 1.12, ensure it's minecraft: prefixed.
    if version == "1.12":
        entity_id = br.prefix(entity_id)


    # Go through all the spawners.
    count = 0
    for teid, pos, te in br.iterate(level, box, br.TES):
        if teid not in SPAWNER_TEID: # Ignore non-spawners.
            continue

        # Check the correct place for each version.
        matches = False

        if version == "1.8":
            if has(te, "EntityId", TAG_String):
                matches = (te["EntityId"].value == entity_id)
            else:
                # Scream about bad data.
                print "Malformed spawner (for this version) at: {}".format(pos)

        elif version == "1.12":
            if (has(te, "SpawnData", TAG_Compound) and
                    has(te["SpawnData"], "id", TAG_String)):
                matches = (te["SpawnData"]["id"].value == entity_id)
            else:
                print "Malformed spawner (for this version) at: {}".format(pos)

        # Count and print if it matches.
        if matches:
            count += 1
            print "Found spawner at: {}".format(pos)


    print "Found {} spawner{} with entity id: \"{}\"".format(count,
            "" if count == 1 else "s", entity_id)
    return



def op_list(level, box, options):
    # Go through all the spawners.
    count = 0
    for teid, _, te in br.iterate(level, box, br.TES):
        if teid not in SPAWNER_TEID: # Ignore non-spawners.
            continue
        # Count and print.
        count += 1
        print te


    print "Listed {} spawner{}.".format(count, "" if count == 1 else "s")
    return
