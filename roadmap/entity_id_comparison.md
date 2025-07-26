# Entity ID Format Comparison: Sequence IDs vs UUIDs

## Sequence IDs: `{type}_{name}_{sequence}`
Example: `pc_sariel_001`, `npc_guard_003`, `loc_throne_room_001`

### Pros
1. **Human Readable**: Developers can instantly understand `npc_guard_003` is the third guard NPC
2. **Debugging Friendly**: Logs show "Missing npc_cassian_001" vs "Missing 550e8400-e29b-41d4"
3. **Sortable**: Natural ordering - guard_001, guard_002, guard_003
4. **Semantic Meaning**: ID contains type and name information
5. **Shorter**: Less storage space, easier to type in dev tools
6. **Pattern Matching**: Can query "all guards" with `npc_guard_*`

### Cons
1. **Sequence Management**: Need to track next available number per type/name
2. **Potential Collisions**: If two systems generate IDs independently
3. **Rename Complexity**: If "guard" becomes "knight", ID doesn't match
4. **Campaign Merging**: Conflicts when combining campaigns
5. **Less Unique**: Relies on proper sequence management

## UUIDs: `550e8400-e29b-41d4-a716-446655440000`

### Pros
1. **Guaranteed Unique**: No collision risk even across systems
2. **No Coordination**: Any system can generate IDs independently
3. **Immutable**: Never need to change once created
4. **Industry Standard**: Well-understood, battle-tested
5. **Merge Friendly**: Can combine campaigns without ID conflicts
6. **Distributed Safe**: Multiple servers can create entities

### Cons
1. **Not Human Readable**: "550e8400-e29b-41d4-a716-446655440000" vs "Sariel"
2. **Debugging Harder**: Logs full of UUIDs are difficult to parse
3. **Longer**: 36 characters vs ~15 for sequence IDs
4. **No Semantic Info**: Must lookup to know what entity it represents
5. **No Natural Order**: Can't sort meaningfully
6. **Developer Friction**: Copy-pasting UUIDs is error-prone

## Hybrid Approach (Recommended)

### Option 1: UUID with Type Prefix
```
pc_550e8400-e29b-41d4-a716-446655440000
npc_660f9800-f39c-51e5-b826-557766550000
```

**Pros**: Type visible, globally unique
**Cons**: Still long, not fully readable

### Option 2: Readable ID with UUID Fallback
```json
{
    "entity_id": "pc_sariel_001",          // Human-readable primary
    "uuid": "550e8400-e29b-41d4-a716-446655440000",  // Backup uniqueness
    "entity_type": "pc",
    "display_name": "Sariel Arcanus"
}
```

**Pros**: Best of both worlds
**Cons**: Two IDs to manage

### Option 3: Short UUID with Type
```
pc_8400e29b_sariel   // First 8 chars of UUID + name
npc_9800f39c_guard
```

**Pros**: Shorter, somewhat readable, very low collision risk
**Cons**: Still less readable than sequence

## Recommendation for This Project

**Use Sequence IDs** with these safeguards:

1. **Format**: `{type}_{name}_{sequence}`
2. **Sequence Tracking**: Store next sequence per type/name combo
3. **Campaign Prefix Option**: `sariel_v2.pc_sariel_001` for imports
4. **Validation**: Check for duplicates on creation
5. **Future Migration Path**: Can add UUID field later if needed

### Why Sequence IDs for This Project:

1. **Developer Experience**: You'll be debugging narrative desyncs constantly
2. **Log Readability**: "Missing npc_cassian_001" is instantly clear
3. **Small Scale**: Not building distributed system with millions of entities
4. **Campaign Scope**: IDs only need uniqueness within a campaign
5. **Performance**: Shorter IDs = faster string operations

### Implementation Example:

```python
class EntityIDGenerator:
    def __init__(self):
        self.sequences = {}  # {type_name: next_number}

    def generate_id(self, entity_type: str, base_name: str) -> str:
        """Generate next sequential ID"""
        key = f"{entity_type}_{base_name}"

        if key not in self.sequences:
            self.sequences[key] = 1

        sequence = self.sequences[key]
        self.sequences[key] += 1

        return f"{entity_type}_{base_name}_{sequence:03d}"

# Usage
generator = EntityIDGenerator()
print(generator.generate_id("npc", "guard"))      # npc_guard_001
print(generator.generate_id("npc", "guard"))      # npc_guard_002
print(generator.generate_id("pc", "sariel"))      # pc_sariel_001
```

### When to Switch to UUIDs:

1. Multiple servers generating entities
2. Merging campaigns becomes common
3. Need to federate across systems
4. ID collisions become a real problem
5. Building public API where IDs are exposed

For now, **sequence IDs** will make development and debugging much easier while still providing the structure needed for robust entity tracking.
