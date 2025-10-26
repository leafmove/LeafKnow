"use client"

// import { AlertCircle } from "lucide-react"
import React, { useState } from "react"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs"
import {
  COMMON_STYLES,
  DEFAULT_FONT_MONO,
  DEFAULT_FONT_SANS,
  DEFAULT_FONT_SERIF,
  defaultThemeState,
} from "@/tweakcn/config/theme"

import { useEditorStore } from "@/tweakcn/store/editor-store"
import {
  ThemeEditorControlsProps,
  ThemeStyleProps,
} from "@/tweakcn/types/theme"
import {
  getAppliedThemeFont,
  monoFonts,
  sansSerifFonts,
  serifFonts,
} from "@/tweakcn/utils/theme-fonts"
import ColorPicker from "./color-picker"
import ControlSection from "./control-section"
import HslAdjustmentControls from "./hsl-adjustment-controls"
import ShadowControl from "./shadow-control"
import { SliderWithInput } from "./slider-with-input"
import ThemeEditActions from "./theme-edit-actions"
import ThemeFontSelect from "./theme-font-select"
import ThemePresetSelect from "./theme-preset-select"
import TabsTriggerPill from "./theme-preview/tabs-trigger-pill"

const ThemeControlPanel = ({
  styles,
  currentMode,
  onChange,
}: ThemeEditorControlsProps) => {
  const { themeState } = useEditorStore()
  const [tab, setTab] = useState("colors")

  const currentStyles = React.useMemo(
    () => ({
      ...defaultThemeState.styles[currentMode],
      ...styles?.[currentMode],
    }),
    [currentMode, styles]
  )

  const updateStyle = React.useCallback(
    <K extends keyof typeof currentStyles>(
      key: K,
      value: (typeof currentStyles)[K]
    ) => {
      // apply common styles to both light and dark modes
      if (COMMON_STYLES.includes(key)) {
        onChange({
          ...styles,
          light: { ...styles.light, [key]: value },
          dark: { ...styles.dark, [key]: value },
        })
        return
      }

      onChange({
        ...styles,
        [currentMode]: {
          ...currentStyles,
          [key]: value,
        },
      })
    },
    [onChange, styles, currentMode, currentStyles]
  )

  // Ensure we have valid styles for the current mode
  if (!currentStyles) {
    return null // Or some fallback UI
  }

  const radius = parseFloat(currentStyles.radius?.replace("rem", "") || "0")

  const theme = null

  return (
    <>
      <div className="border-b flex items-center">
        {!theme ? (
          <ThemePresetSelect className="h-14 rounded-none" />
        ) : (
          <ThemeEditActions theme={theme} />
        )}
      </div>
      <div className="flex min-h-0 flex-1 flex-col">
        <Tabs
          value={tab}
          onValueChange={setTab}
          className="flex min-h-0 w-full flex-1 flex-col"
        >
          <div className="shrink-0 border-b border-border">
            <div className="mt-2 mb-1 px-4">
              <TabsList className="bg-background text-muted-foreground inline-flex w-fit items-center justify-center rounded-full px-0">
                <TabsTriggerPill value="colors">Colors</TabsTriggerPill>
                <TabsTriggerPill value="typography">Typography</TabsTriggerPill>
                <TabsTriggerPill value="other">Other</TabsTriggerPill>
              </TabsList>
            </div>
          </div>

          <div className="flex-1 min-h-0">
            <TabsContent
              value="colors"
              className="mt-1 h-full"
            >
              <div className="px-4">
                  <div className="space-y-4 pr-5">
                    <ControlSection title="Primary Colors" expanded>
                      <ColorPicker
                        color={currentStyles.primary || ""}
                        onChange={(color) => updateStyle("primary", color)}
                        label="Primary"
                      />
                      <ColorPicker
                        color={currentStyles["primary-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("primary-foreground", color)
                        }
                        label="Primary Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Secondary Colors" expanded>
                      <ColorPicker
                        color={currentStyles.secondary || ""}
                        onChange={(color) => updateStyle("secondary", color)}
                        label="Secondary"
                      />
                      <ColorPicker
                        color={currentStyles["secondary-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("secondary-foreground", color)
                        }
                        label="Secondary Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Accent Colors">
                      <ColorPicker
                        color={currentStyles.accent || ""}
                        onChange={(color) => updateStyle("accent", color)}
                        label="Accent"
                      />
                      <ColorPicker
                        color={currentStyles["accent-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("accent-foreground", color)
                        }
                        label="Accent Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Base Colors">
                      <ColorPicker
                        color={currentStyles.background || ""}
                        onChange={(color) => updateStyle("background", color)}
                        label="Background"
                      />
                      <ColorPicker
                        color={currentStyles.foreground || ""}
                        onChange={(color) => updateStyle("foreground", color)}
                        label="Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Card Colors">
                      <ColorPicker
                        color={currentStyles.card || ""}
                        onChange={(color) => updateStyle("card", color)}
                        label="Card Background"
                      />
                      <ColorPicker
                        color={currentStyles["card-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("card-foreground", color)
                        }
                        label="Card Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Popover Colors">
                      <ColorPicker
                        color={currentStyles.popover || ""}
                        onChange={(color) => updateStyle("popover", color)}
                        label="Popover Background"
                      />
                      <ColorPicker
                        color={currentStyles["popover-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("popover-foreground", color)
                        }
                        label="Popover Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Muted Colors">
                      <ColorPicker
                        color={currentStyles.muted || ""}
                        onChange={(color) => updateStyle("muted", color)}
                        label="Muted"
                      />
                      <ColorPicker
                        color={currentStyles["muted-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("muted-foreground", color)
                        }
                        label="Muted Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Destructive Colors">
                      <ColorPicker
                        color={currentStyles.destructive || ""}
                        onChange={(color) => updateStyle("destructive", color)}
                        label="Destructive"
                      />
                      <ColorPicker
                        color={currentStyles["destructive-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("destructive-foreground", color)
                        }
                        label="Destructive Foreground"
                      />
                    </ControlSection>

                    <ControlSection title="Border & Input Colors">
                      <ColorPicker
                        color={currentStyles.border || ""}
                        onChange={(color) => updateStyle("border", color)}
                        label="Border"
                      />
                      <ColorPicker
                        color={currentStyles.input || ""}
                        onChange={(color) => updateStyle("input", color)}
                        label="Input"
                      />
                      <ColorPicker
                        color={currentStyles.ring || ""}
                        onChange={(color) => updateStyle("ring", color)}
                        label="Ring"
                      />
                    </ControlSection>

                    <ControlSection title="Chart Colors">
                      <ColorPicker
                        color={currentStyles["chart-1"] || ""}
                        onChange={(color) => updateStyle("chart-1", color)}
                        label="Chart 1"
                      />
                      <ColorPicker
                        color={currentStyles["chart-2"] || ""}
                        onChange={(color) => updateStyle("chart-2", color)}
                        label="Chart 2"
                      />
                      <ColorPicker
                        color={currentStyles["chart-3"] || ""}
                        onChange={(color) => updateStyle("chart-3", color)}
                        label="Chart 3"
                      />
                      <ColorPicker
                        color={currentStyles["chart-4"] || ""}
                        onChange={(color) => updateStyle("chart-4", color)}
                        label="Chart 4"
                      />
                      <ColorPicker
                        color={currentStyles["chart-5"] || ""}
                        onChange={(color) => updateStyle("chart-5", color)}
                        label="Chart 5"
                      />
                    </ControlSection>

                    <ControlSection title="Sidebar Colors">
                      <ColorPicker
                        color={currentStyles.sidebar || ""}
                        onChange={(color) => updateStyle("sidebar", color)}
                        label="Sidebar Background"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("sidebar-foreground", color)
                        }
                        label="Sidebar Foreground"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-primary"] || ""}
                        onChange={(color) =>
                          updateStyle("sidebar-primary", color)
                        }
                        label="Sidebar Primary"
                      />
                      <ColorPicker
                        color={
                          currentStyles["sidebar-primary-foreground"] || ""
                        }
                        onChange={(color) =>
                          updateStyle("sidebar-primary-foreground", color)
                        }
                        label="Sidebar Primary Foreground"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-accent"] || ""}
                        onChange={(color) =>
                          updateStyle("sidebar-accent", color)
                        }
                        label="Sidebar Accent"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-accent-foreground"] || ""}
                        onChange={(color) =>
                          updateStyle("sidebar-accent-foreground", color)
                        }
                        label="Sidebar Accent Foreground"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-border"] || ""}
                        onChange={(color) =>
                          updateStyle("sidebar-border", color)
                        }
                        label="Sidebar Border"
                      />
                      <ColorPicker
                        color={currentStyles["sidebar-ring"] || ""}
                        onChange={(color) => updateStyle("sidebar-ring", color)}
                        label="Sidebar Ring"
                      />
                    </ControlSection>
                  </div>
              </div>
            </TabsContent>

            <TabsContent
              value="typography"
              className="mt-1 size-full overflow-hidden"
            >
              <div className="px-4">
                  <div className="space-y-4 pr-5">
                    {/* <div className="bg-muted/50 mb-4 flex items-start gap-2.5 rounded-md border p-3">
                      <AlertCircle className="text-muted-foreground mt-0.5 h-5 w-5 shrink-0" />
                      <div className="text-muted-foreground text-sm">
                        <p>
                          To use custom fonts, embed them in your project.{" "}
                          <br />
                          See{" "}
                          <a
                            href="https://tailwindcss.com/docs/font-family"
                            target="_blank"
                            className="hover:text-muted-foreground/90 underline underline-offset-2"
                          >
                            Tailwind docs
                          </a>{" "}
                          for details.
                        </p>
                      </div>
                    </div> */}

                    <ControlSection title="Font Family" expanded>
                      <div className="mb-4">
                        <Label
                          htmlFor="font-sans"
                          className="mb-1.5 block text-xs"
                        >
                          Sans-Serif Font
                        </Label>
                        <ThemeFontSelect
                          fonts={{
                            ...sansSerifFonts,
                            ...serifFonts,
                            ...monoFonts,
                          }}
                          defaultValue={DEFAULT_FONT_SANS}
                          currentFont={getAppliedThemeFont(
                            themeState,
                            "font-sans"
                          )}
                          onFontChange={(value) =>
                            updateStyle("font-sans", value)
                          }
                        />
                      </div>

                      <Separator className="my-4" />

                      <div className="mb-4">
                        <Label
                          htmlFor="font-serif"
                          className="mb-1.5 block text-xs"
                        >
                          Serif Font
                        </Label>
                        <ThemeFontSelect
                          fonts={{
                            ...serifFonts,
                            ...sansSerifFonts,
                            ...monoFonts,
                          }}
                          defaultValue={DEFAULT_FONT_SERIF}
                          currentFont={getAppliedThemeFont(
                            themeState,
                            "font-serif"
                          )}
                          onFontChange={(value) =>
                            updateStyle("font-serif", value)
                          }
                        />
                      </div>

                      <Separator className="my-4" />
                      <div>
                        <Label
                          htmlFor="font-mono"
                          className="mb-1.5 block text-xs"
                        >
                          Monospace Font
                        </Label>
                        <ThemeFontSelect
                          fonts={{
                            ...monoFonts,
                            ...sansSerifFonts,
                            ...serifFonts,
                          }}
                          defaultValue={DEFAULT_FONT_MONO}
                          currentFont={getAppliedThemeFont(
                            themeState,
                            "font-mono"
                          )}
                          onFontChange={(value) =>
                            updateStyle("font-mono", value)
                          }
                        />
                      </div>
                    </ControlSection>

                    <ControlSection title="Letter Spacing" expanded>
                      <SliderWithInput
                        value={parseFloat(
                          currentStyles["letter-spacing"]?.replace("em", "") ||
                            "0"
                        )}
                        onChange={(value) =>
                          updateStyle("letter-spacing", `${value}em`)
                        }
                        min={-0.5}
                        max={0.5}
                        step={0.025}
                        unit="em"
                        label="Letter Spacing"
                      />
                    </ControlSection>
                  </div>
              </div>
            </TabsContent>

            <TabsContent
              value="other"
              className="mt-1 size-full overflow-hidden"
            >
              <div className="px-4">
                  <div className="space-y-4 pr-5">
                    <ControlSection title="HSL Adjustments" expanded>
                      <HslAdjustmentControls />
                    </ControlSection>

                    <ControlSection title="Radius" expanded>
                      <SliderWithInput
                        value={radius}
                        onChange={(value) =>
                          updateStyle("radius", `${value}rem`)
                        }
                        min={0}
                        max={5}
                        step={0.025}
                        unit="rem"
                        label="Radius"
                      />
                    </ControlSection>

                    <ControlSection title="Spacing">
                      <SliderWithInput
                        value={parseFloat(
                          currentStyles.spacing?.replace("rem", "") || "0.25"
                        )}
                        onChange={(value) =>
                          updateStyle("spacing", `${value}rem`)
                        }
                        min={0.15}
                        max={0.35}
                        step={0.01}
                        unit="rem"
                        label="Spacing"
                      />
                    </ControlSection>

                    <ControlSection title="Shadow">
                      <ShadowControl
                        shadowColor={currentStyles["shadow-color"] || ""}
                        shadowOpacity={parseFloat(
                          currentStyles["shadow-opacity"] || "0"
                        )}
                        shadowBlur={parseFloat(
                          currentStyles["shadow-blur"]?.replace("px", "") || "0"
                        )}
                        shadowSpread={parseFloat(
                          currentStyles["shadow-spread"]?.replace("px", "") ||
                            "0"
                        )}
                        shadowOffsetX={parseFloat(
                          currentStyles["shadow-offset-x"]?.replace("px", "") ||
                            "0"
                        )}
                        shadowOffsetY={parseFloat(
                          currentStyles["shadow-offset-y"]?.replace("px", "") ||
                            "0"
                        )}
                        onChange={(key, value) => {
                          if (key === "shadow-color") {
                            updateStyle(key, value as string)
                          } else if (key === "shadow-opacity") {
                            updateStyle(key, value.toString())
                          } else {
                            updateStyle(
                              key as keyof ThemeStyleProps,
                              `${value}px`
                            )
                          }
                        }}
                      />
                    </ControlSection>
                  </div>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </>
  )
}

export default ThemeControlPanel
