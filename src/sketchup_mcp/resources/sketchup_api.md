# SketchUp Ruby API Reference (2017 Compatible)

This reference covers the SketchUp Ruby API for use with `eval_ruby`. All code
must be compatible with SketchUp Make 2017 (Ruby 2.2.4).

## Important: Ruby 2.2.4 Compatibility

SketchUp 2017 uses Ruby 2.2.4. Avoid these newer Ruby features:
- No safe navigation operator (`&.`) - use `obj && obj.method` instead
- No `Array#dig` or `Hash#dig` - use nested access with checks
- No keyword argument shortcuts
- No `itself` method

## Core Objects

### Getting the Model

```ruby
model = Sketchup.active_model      # Current model
entities = model.active_entities   # Entities in current context
selection = model.selection        # Selected items
materials = model.materials        # Material library
```

### Model Properties

```ruby
model.name                    # Model name
model.path                    # File path (empty if unsaved)
model.modified?               # Has unsaved changes
model.bounds                  # Bounding box of entire model
```

## Creating Geometry

### Groups

Groups contain geometry and can be transformed as a unit.

```ruby
# Create an empty group
group = entities.add_group

# Create geometry inside the group
group.entities.add_face(pt1, pt2, pt3, pt4)

# Group properties
group.entityID               # Unique ID
group.name = "My Group"      # Set name
group.bounds                 # Bounding box
```

### Faces

Faces are flat surfaces defined by edges.

```ruby
# Create a rectangular face (points in counter-clockwise order for front face up)
face = entities.add_face(
  [0, 0, 0],
  [100, 0, 0],
  [100, 100, 0],
  [0, 100, 0]
)

# Extrude the face
face.pushpull(50)    # Extrude 50 units

# Face properties
face.area            # Surface area
face.normal          # Normal vector
face.vertices        # Corner vertices
face.edges           # Boundary edges
```

### Edges and Lines

```ruby
# Create a single edge
edge = entities.add_line([0,0,0], [100,0,0])

# Create multiple connected edges
edges = entities.add_edges(pt1, pt2, pt3, pt4)

# Create a circle (returns array of edges)
center = [50, 50, 0]
normal = [0, 0, 1]
radius = 25
edges = entities.add_circle(center, normal, radius)
```

### Arcs and Curves

```ruby
# Create an arc
center = [0, 0, 0]
xaxis = [1, 0, 0]
normal = [0, 0, 1]
radius = 50
start_angle = 0
end_angle = Math::PI / 2   # 90 degrees
edges = entities.add_arc(center, xaxis, normal, radius, start_angle, end_angle)
```

## Transformations

### Creating Transformations

```ruby
# Translation (move)
move = Geom::Transformation.translation([10, 20, 30])

# Rotation around axis
center = [0, 0, 0]
axis = [0, 0, 1]      # Z-axis
angle = 45.degrees    # SketchUp adds .degrees method
rotation = Geom::Transformation.rotation(center, axis, angle)

# Scaling
uniform_scale = Geom::Transformation.scaling(2.0)
non_uniform = Geom::Transformation.scaling(center, 2.0, 1.0, 0.5)

# Combine transformations
combined = move * rotation * uniform_scale
```

### Applying Transformations

```ruby
# Transform an entity
entity.transform!(transformation)

# Move to specific location
entity.transformation = Geom::Transformation.new([x, y, z])
```

## Materials

### Creating and Applying Materials

```ruby
# Create a material
mat = model.materials.add("Pine")
mat.color = Sketchup::Color.new(210, 180, 140)

# Apply to a face
face.material = mat
face.back_material = mat

# Apply to all faces in a group
group.entities.grep(Sketchup::Face).each { |f| f.material = mat }

# Named colors
mat.color = "Red"
mat.color = Sketchup::Color.new(255, 0, 0)
mat.color = Sketchup::Color.new("#FF0000")
```

### Common Wood Colors

```ruby
# Pine
Sketchup::Color.new(210, 180, 140)

# Oak
Sketchup::Color.new(180, 140, 100)

# Walnut
Sketchup::Color.new(90, 60, 40)

# Cherry
Sketchup::Color.new(150, 80, 60)

# Maple
Sketchup::Color.new(230, 210, 180)
```

## Working with Selection

```ruby
# Get selected entities
selection = model.selection
selection.count              # Number of selected items
selection.empty?             # True if nothing selected

# Iterate over selection
selection.each do |entity|
  puts entity.typename       # "Group", "Face", "Edge", etc.
  puts entity.entityID
end

# Modify selection
selection.clear
selection.add(entity)
selection.remove(entity)
selection.toggle(entity)
```

## Finding Entities

```ruby
# Find by ID
entity = model.find_entity_by_id(12345)

# Find by type
groups = entities.grep(Sketchup::Group)
faces = entities.grep(Sketchup::Face)
edges = entities.grep(Sketchup::Edge)
components = entities.grep(Sketchup::ComponentInstance)
```

## Common Recipes

### Create a Board (Rectangular Prism)

```ruby
def create_board(width, height, depth, position = [0,0,0])
  model = Sketchup.active_model
  entities = model.active_entities

  group = entities.add_group
  x, y, z = position

  # Create bottom face
  face = group.entities.add_face(
    [x, y, z],
    [x + width, y, z],
    [x + width, y + depth, z],
    [x, y + depth, z]
  )

  # Extrude to height
  face.pushpull(height)

  group
end

# Usage: create_board(100, 20, 50, [0, 0, 0])
```

### Create a Dado (Groove)

```ruby
def create_dado(board_group, dado_width, dado_depth, position_along_board)
  # Get board dimensions from bounds
  bounds = board_group.bounds
  board_width = bounds.width
  board_height = bounds.height

  # Create cutting group
  model = Sketchup.active_model
  cutter = model.active_entities.add_group

  x = bounds.min.x + position_along_board
  y = bounds.min.y
  z = bounds.min.z

  face = cutter.entities.add_face(
    [x, y, z],
    [x + dado_width, y, z],
    [x + dado_width, y, z + dado_depth],
    [x, y, z + dado_depth]
  )
  face.pushpull(board_height)

  # Subtract cutter from board (requires manual intersection in Make 2017)
  cutter
end
```

### Apply Material to Group

```ruby
def apply_material_to_group(group, color_or_name)
  model = Sketchup.active_model

  # Get or create material
  mat = model.materials[color_or_name]
  if mat.nil?
    mat = model.materials.add(color_or_name)
    mat.color = color_or_name
  end

  # Apply to all faces
  group.entities.grep(Sketchup::Face).each do |face|
    face.material = mat
    face.back_material = mat
  end
end
```

### Get Bounding Box Info

```ruby
def get_bounds_info(entity)
  bounds = entity.bounds
  {
    width: bounds.width,
    height: bounds.height,
    depth: bounds.depth,
    center: bounds.center.to_a,
    min: bounds.min.to_a,
    max: bounds.max.to_a
  }
end
```

## Units

SketchUp internally uses inches. Convert as needed:

```ruby
# Convert to inches (internal unit)
mm_to_inch = 1.0 / 25.4
cm_to_inch = 1.0 / 2.54

# Or use SketchUp's conversion
100.mm                    # 100mm in inches
10.cm                     # 10cm in inches
1.m                       # 1 meter in inches
1.feet                    # 1 foot in inches
```

## Error Handling

Always wrap risky operations:

```ruby
begin
  # Your code here
  model = Sketchup.active_model
  result = model.entities.add_face(points)
rescue => e
  puts "Error: #{e.message}"
  nil
end
```

## Operations (Undo Support)

Wrap changes in an operation for single undo:

```ruby
model = Sketchup.active_model
model.start_operation("Create Bookshelf", true)

begin
  # Create geometry here
  # ...
  model.commit_operation
rescue => e
  model.abort_operation
  raise e
end
```
