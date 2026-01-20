require 'sketchup'
require 'json'
require 'socket'
require 'fileutils'

puts "MCP Extension loading..."
SKETCHUP_CONSOLE.show rescue nil

module SU_MCP
  class Server
    def initialize
      @port = 9876
      @server = nil
      @running = false
      @timer_id = nil

      begin
        SKETCHUP_CONSOLE.show
      rescue
        begin
          Sketchup.send_action("showRubyPanel:")
        rescue
          UI.start_timer(0) { SKETCHUP_CONSOLE.show }
        end
      end
    end

    def log(msg)
      begin
        SKETCHUP_CONSOLE.write("MCP: #{msg}\n")
      rescue
        puts "MCP: #{msg}"
      end
      STDOUT.flush
    end

    def start
      return if @running

      begin
        log "Starting server on localhost:#{@port}..."

        @server = TCPServer.new('127.0.0.1', @port)
        log "Server created on port #{@port}"

        @running = true

        @timer_id = UI.start_timer(0.1, true) {
          begin
            if @running
              ready = IO.select([@server], nil, nil, 0)
              if ready
                log "Connection waiting..."
                client = nil
                begin
                  client = @server.accept_nonblock
                  log "Client accepted"

                  unless authenticate(client)
                    log "Authentication failed"
                    next
                  end

                  data = client.gets
                  log "Raw data: #{data.inspect}"

                  if data
                    begin
                      request = JSON.parse(data)
                      log "Parsed request: #{request.inspect}"

                      response = handle_request(request)
                      response_json = response.to_json + "\n"

                      log "Sending response: #{response_json.strip}"
                      client.write(response_json)
                      client.flush
                      log "Response sent"
                    rescue JSON::ParserError => e
                      log "JSON parse error: #{e.message}"
                      error_response = {
                        jsonrpc: "2.0",
                        error: { code: -32700, message: "Parse error: #{e.message}" },
                        id: nil
                      }.to_json + "\n"
                      client.write(error_response)
                      client.flush
                    rescue StandardError => e
                      log "Request error: #{e.message}"
                      log e.backtrace.first(5).join("\n")
                      error_response = {
                        jsonrpc: "2.0",
                        error: { code: -32603, message: e.message },
                        id: request ? request["id"] : nil
                      }.to_json + "\n"
                      client.write(error_response)
                      client.flush
                    end
                  end
                ensure
                  client&.close
                  log "Client closed" if client
                end
              end
            end
          rescue IO::WaitReadable
            # Normal for accept_nonblock
          rescue StandardError => e
            log "Timer error: #{e.message}"
            log e.backtrace.first(3).join("\n")
          end
        }

        log "Server started and listening"

      rescue StandardError => e
        log "Error: #{e.message}"
        log e.backtrace.first(5).join("\n")
        stop
      end
    end

    def stop
      log "Stopping server..."
      @running = false

      if @timer_id
        UI.stop_timer(@timer_id)
        @timer_id = nil
      end

      @server.close if @server
      @server = nil
      log "Server stopped"
    end

    private

    def authenticate(client)
      secret = ENV['SKETCHUP_MCP_SECRET']
      return true if secret.nil? || secret.empty?

      auth_data = client.gets
      return false unless auth_data

      provided = JSON.parse(auth_data)["secret"] rescue nil
      provided == secret
    end

    def handle_request(request)
      log "Handling request: #{request["method"]}"

      case request["method"]
      when "tools/call"
        handle_tool_call(request)
      when "ping"
        {
          jsonrpc: "2.0",
          result: { status: "ok" },
          id: request["id"]
        }
      else
        {
          jsonrpc: "2.0",
          error: { code: -32601, message: "Method not found: #{request["method"]}" },
          id: request["id"]
        }
      end
    end

    def handle_tool_call(request)
      tool_name = request.dig("params", "name")
      args = request.dig("params", "arguments") || {}

      log "Tool call: #{tool_name}"

      begin
        result = case tool_name
        when "eval_ruby"
          eval_ruby(args)
        when "describe_model"
          describe_model(args)
        when "export_scene"
          export_scene(args)
        else
          raise "Unknown tool: #{tool_name}"
        end

        {
          jsonrpc: "2.0",
          result: {
            content: [{ type: "text", text: result[:text] || result.to_json }],
            isError: false
          },
          id: request["id"]
        }
      rescue StandardError => e
        log "Tool error: #{e.message}"
        log e.backtrace.first(5).join("\n")
        {
          jsonrpc: "2.0",
          result: {
            content: [{ type: "text", text: "Error: #{e.message}" }],
            isError: true
          },
          id: request["id"]
        }
      end
    end

    def eval_ruby(args)
      code = args["code"]
      raise "No code provided" unless code && !code.empty?

      log "Evaluating Ruby code (#{code.length} chars)"

      begin
        result = eval(code, TOPLEVEL_BINDING)
        log "Eval result: #{result.inspect}"

        { text: result.to_s }
      rescue SyntaxError => e
        raise "Syntax error: #{e.message}"
      rescue StandardError => e
        raise "Runtime error: #{e.message}"
      end
    end

    def describe_model(args)
      model = Sketchup.active_model
      raise "No active model" unless model

      entities = model.active_entities

      groups = entities.grep(Sketchup::Group)
      components = entities.grep(Sketchup::ComponentInstance)
      faces = entities.grep(Sketchup::Face)
      edges = entities.grep(Sketchup::Edge)

      selection = model.selection

      description = {
        name: model.name.empty? ? "Untitled" : model.name,
        path: model.path.empty? ? nil : model.path,
        units: model.options["UnitsOptions"]["LengthUnit"],
        entities: {
          total: entities.length,
          groups: groups.length,
          components: components.length,
          faces: faces.length,
          edges: edges.length
        },
        selection: {
          count: selection.length,
          items: selection.first(10).map { |e|
            { id: e.entityID, type: e.typename }
          }
        },
        bounds: model_bounds(model)
      }

      if args["include_details"]
        description[:groups] = groups.first(20).map { |g|
          {
            id: g.entityID,
            name: g.name,
            bounds: entity_bounds(g)
          }
        }
        description[:components] = components.first(20).map { |c|
          {
            id: c.entityID,
            name: c.definition.name,
            bounds: entity_bounds(c)
          }
        }
      end

      { text: JSON.pretty_generate(description) }
    end

    def export_scene(args)
      model = Sketchup.active_model
      raise "No active model" unless model

      format = (args["format"] || "skp").downcase

      temp_dir = File.join(ENV['TEMP'] || ENV['TMP'] || Dir.tmpdir, "sketchup_exports")
      FileUtils.mkdir_p(temp_dir) unless Dir.exist?(temp_dir)

      timestamp = Time.now.strftime("%Y%m%d_%H%M%S")
      filename = "export_#{timestamp}"

      case format
      when "skp"
        export_path = File.join(temp_dir, "#{filename}.skp")
        model.save(export_path)
      when "png", "jpg", "jpeg"
        ext = format == "jpg" ? "jpeg" : format
        export_path = File.join(temp_dir, "#{filename}.#{ext}")

        view = model.active_view
        options = {
          filename: export_path,
          width: args["width"] || 1920,
          height: args["height"] || 1080,
          antialias: true,
          transparent: (ext == "png")
        }
        view.write_image(options)
      else
        raise "Unsupported format: #{format}. Supported: skp, png, jpg"
      end

      log "Exported to: #{export_path}"
      { text: "Exported to: #{export_path}" }
    end

    def model_bounds(model)
      bounds = model.bounds
      return nil if bounds.empty?

      {
        min: [bounds.min.x, bounds.min.y, bounds.min.z],
        max: [bounds.max.x, bounds.max.y, bounds.max.z],
        width: bounds.width,
        height: bounds.height,
        depth: bounds.depth
      }
    end

    def entity_bounds(entity)
      bounds = entity.bounds
      return nil if bounds.empty?

      {
        min: [bounds.min.x, bounds.min.y, bounds.min.z],
        max: [bounds.max.x, bounds.max.y, bounds.max.z],
        width: bounds.width,
        height: bounds.height,
        depth: bounds.depth
      }
    end
  end

  unless file_loaded?(__FILE__)
    @server = Server.new

    menu = UI.menu("Plugins").add_submenu("MCP Server")
    menu.add_item("Start Server") { @server.start }
    menu.add_item("Stop Server") { @server.stop }

    file_loaded(__FILE__)
  end
end
