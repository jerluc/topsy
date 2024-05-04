import OpenGL.GL as gl
import glfw
import imgui
import sys

from imgui.integrations.glfw import GlfwRenderer

from topsy.config import find_state_dir, load as load_config
from topsy.plugins import init_plugins, safe_process, safe_close


def load_settings():
    state_path = find_state_dir() / "imgui.ini"
    imgui.load_ini_settings_from_disk(state_path.as_posix())


def save_settings():
    state_path = find_state_dir() / "imgui.ini"
    imgui.save_ini_settings_to_disk(state_path.as_posix())


def main():
    config = load_config()
    plugins = init_plugins(config.plugins)

    imgui.create_context()

    load_settings()

    window = impl_glfw_init()
    impl = GlfwRenderer(window)

    show_style_editor = False

    style = imgui.get_style()
    window_bg = style.color(imgui.COLOR_WINDOW_BACKGROUND)
    imgui.push_style_color(
        imgui.COLOR_WINDOW_BACKGROUND, window_bg.x, window_bg.y, window_bg.z, 1.0
    )
    frame_bg = style.color(imgui.COLOR_FRAME_BACKGROUND)
    imgui.push_style_color(
        imgui.COLOR_FRAME_BACKGROUND, frame_bg.x, frame_bg.y, frame_bg.z, 1.0
    )
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, [8, 8])
    imgui.push_style_color(imgui.COLOR_BORDER, 1.0, 1.0, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 2)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        io = imgui.get_io()

        if imgui.is_key_pressed(glfw.KEY_ESCAPE):
            break

        if io.key_shift and imgui.is_key_pressed(glfw.KEY_SLASH):
            show_style_editor = not show_style_editor

        imgui.new_frame()

        if show_style_editor:
            imgui.show_style_editor()
            imgui.show_metrics_window()

        safe_process(plugins)
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()

        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    safe_close(plugins)
    impl.shutdown()
    glfw.terminate()

    save_settings()


def impl_glfw_init():
    maj, min, _ = glfw.get_version()
    supports_mouse_passthrough = maj >= 3 and min >= 4

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Make it a floating window
    glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
    glfw.window_hint(glfw.FLOATING, glfw.TRUE)
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    # glfw.window_hint(glfw.MAXIMIZED, glfw.TRUE)
    # glfw.window_hint(glfw.FOCUSED, glfw.TRUE)
    if supports_mouse_passthrough:
        glfw.window_hint(glfw.MOUSE_PASSTHROUGH, glfw.TRUE)

    # Create the window and its OpenGL context
    monitor = glfw.get_primary_monitor()
    x, y, width, height = glfw.get_monitor_workarea(monitor)
    window_name = "topsy"
    window = glfw.create_window(width, height, window_name, None, None)
    glfw.set_window_pos(window, x, y)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window


if __name__ == "__main__":
    main()
