import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  Heart,
  Moon,
  Search,
  Settings,
  Shuffle,
  Sun,
} from "lucide-react";
import React, { useCallback, useMemo, useState } from "react";
import { useTheme } from "@/tweakcn/components/theme-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandItem } from "@/components/ui/command";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/tweakcn/lib/utils";
import { useEditorStore } from "@/tweakcn/store/editor-store";
import { useThemePresetStore } from "@/tweakcn/store/theme-preset-store";
import { ThemePreset } from "@/tweakcn/types/theme";
import { getPresetThemeStyles } from "@/tweakcn/utils/theme-preset-helper";

interface ThemePresetSelectProps extends React.ComponentProps<typeof Button> {
  withCycleThemes?: boolean;
}

interface ColorBoxProps {
  color: string;
}

const ColorBox: React.FC<ColorBoxProps> = ({ color }) => (
  <div className="border-muted h-3 w-3 rounded-sm border" style={{ backgroundColor: color }} />
);

interface ThemeColorsProps {
  presetName: string;
  mode: "light" | "dark";
}

const ThemeColors: React.FC<ThemeColorsProps> = ({ presetName, mode }) => {
  const styles = getPresetThemeStyles(presetName)[mode];
  return (
    <div className="flex gap-0.5">
      <ColorBox color={styles.primary} />
      <ColorBox color={styles.accent} />
      <ColorBox color={styles.secondary} />
      <ColorBox color={styles.border} />
    </div>
  );
};

const isThemeNew = (preset: ThemePreset) => {
  if (!preset.createdAt) return false;
  const createdAt = new Date(preset.createdAt);
  const timePeriod = new Date();
  timePeriod.setDate(timePeriod.getDate() - 5);
  return createdAt > timePeriod;
};

const ThemeControls = () => {
  const applyThemePreset = useEditorStore((store) => store.applyThemePreset);
  const presets = useThemePresetStore((store) => store.getAllPresets());

  const presetNames = useMemo(() => ["default", ...Object.keys(presets)], [presets]);

  const randomize = useCallback(() => {
    const random = Math.floor(Math.random() * presetNames.length);
    applyThemePreset(presetNames[random]);
  }, [presetNames, applyThemePreset]);

  const { theme, toggleTheme } = useTheme();
  const handleThemeToggle = (event: React.MouseEvent<HTMLButtonElement>) => {
    const { clientX: x, clientY: y } = event;
    toggleTheme({ x, y });
  };

  return (
    <TooltipProvider>
      <div className="flex gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={handleThemeToggle}>
              {theme === "light" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs">Toggle theme</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={randomize}>
              <Shuffle className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="text-xs">Random theme</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
};

interface ThemeCycleButtonProps extends React.ComponentProps<typeof Button> {
  direction: "prev" | "next";
}

const ThemeCycleButton: React.FC<ThemeCycleButtonProps> = ({
  direction,
  onClick,
  className,
  ...props
}) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <Button
        variant="ghost"
        size="icon"
        className={cn("aspect-square h-full shrink-0 w-8 min-w-8", className)}
        onClick={onClick}
        {...props}
      >
        {direction === "prev" ? (
          <ArrowLeft className="h-4 w-4" />
        ) : (
          <ArrowRight className="h-4 w-4" />
        )}
      </Button>
    </TooltipTrigger>
    <TooltipContent>{direction === "prev" ? "Previous theme" : "Next theme"}</TooltipContent>
  </Tooltip>
);

interface ThemePresetCycleControlsProps extends React.ComponentProps<typeof Button> {
  filteredPresets: string[];
  currentPresetName: string;
  className?: string;
}

const ThemePresetCycleControls: React.FC<ThemePresetCycleControlsProps> = ({
  filteredPresets,
  currentPresetName,
  className,
  ...props
}) => {
  const applyThemePreset = useEditorStore((store) => store.applyThemePreset);
  const { theme, toggleTheme } = useTheme();

  const currentIndex =
    useMemo(
      () => filteredPresets.indexOf(currentPresetName || "default"),
      [filteredPresets, currentPresetName]
    ) ?? 0;

  const cycleTheme = useCallback(
    (direction: "prev" | "next") => {
      const newIndex =
        direction === "next"
          ? (currentIndex + 1) % filteredPresets.length
          : (currentIndex - 1 + filteredPresets.length) % filteredPresets.length;
      applyThemePreset(filteredPresets[newIndex]);
    },
    [currentIndex, filteredPresets, applyThemePreset]
  );

  const handleThemeToggle = (event: React.MouseEvent<HTMLButtonElement>) => {
    const { clientX: x, clientY: y } = event;
    toggleTheme({ x, y });
  };

  return (
    <>
      <Separator orientation="vertical" className="min-h-8" />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon" 
            className={cn("aspect-square min-h-8 w-8 min-w-8", className)}
            onClick={handleThemeToggle}
            {...props}
          >
            {theme === "light" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p className="text-xs">切换明暗模式</p>
        </TooltipContent>
      </Tooltip>

      <Separator orientation="vertical" className="min-h-8" />

      <ThemeCycleButton
        direction="prev"
        size="icon"
        className={cn("aspect-square min-h-8 w-8 min-w-8", className)}
        onClick={() => cycleTheme("prev")}
        {...props}
      />

      <Separator orientation="vertical" className="min-h-8" />

      <ThemeCycleButton
        direction="next"
        size="icon"
        className={cn("aspect-square min-h-8 w-8 min-w-8", className)}
        onClick={() => cycleTheme("next")}
        {...props}
      />
    </>
  );
};

const ThemePresetSelect: React.FC<ThemePresetSelectProps> = ({
  withCycleThemes = true,
  className,
  ...props
}) => {
  const themeState = useEditorStore((store) => store.themeState);
  const applyThemePreset = useEditorStore((store) => store.applyThemePreset);
  const hasUnsavedChanges = useEditorStore((store) => store.hasUnsavedChanges);
  const currentPreset = themeState.preset;
  const mode = themeState.currentMode;

  const presets = useThemePresetStore((store) => store.getAllPresets());

  const [search, setSearch] = useState("");

  const isSavedTheme = useCallback(
    (presetId: string) => {
      return presets[presetId]?.source === "SAVED";
    },
    [presets]
  );

  const presetNames = useMemo(() => ["default", ...Object.keys(presets)], [presets]);
  const currentPresetName = presetNames?.find((name) => name === currentPreset);

  const filteredPresets = useMemo(() => {
    const filteredList =
      search.trim() === ""
        ? presetNames
        : Object.entries(presets)
            .filter(([_, preset]) => preset.label?.toLowerCase().includes(search.toLowerCase()))
            .map(([name]) => name);

    // Separate saved and default themes
    const savedThemesList = filteredList.filter((name) => name !== "default" && isSavedTheme(name));
    const defaultThemesList = filteredList.filter((name) => !savedThemesList.includes(name));

    // Sort each list
    const sortThemes = (list: string[]) =>
      list.sort((a, b) => {
        const labelA = presets[a]?.label || a;
        const labelB = presets[b]?.label || b;
        return labelA.localeCompare(labelB);
      });

    // Combine saved themes first, then default themes
    return [...sortThemes(savedThemesList), ...sortThemes(defaultThemesList)];
  }, [presetNames, search, presets, isSavedTheme]);

  const filteredSavedThemes = useMemo(() => {
    return filteredPresets.filter((name) => name !== "default" && isSavedTheme(name));
  }, [filteredPresets, isSavedTheme]);

  const filteredDefaultThemes = useMemo(() => {
    return filteredPresets.filter((name) => name === "default" || !isSavedTheme(name));
  }, [filteredPresets, isSavedTheme]);

  return (
    <div className="flex w-full items-center">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            className={cn("group relative flex-1 justify-between md:min-w-56", className)}
            {...props}
          >
            <div className="flex w-full items-center gap-3 overflow-hidden">
              <div className="flex gap-0.5">
                <ColorBox color={themeState.styles[mode].primary} />
                <ColorBox color={themeState.styles[mode].accent} />
                <ColorBox color={themeState.styles[mode].secondary} />
                <ColorBox color={themeState.styles[mode].border} />
              </div>
              {currentPresetName !== "default" &&
                currentPresetName &&
                isSavedTheme(currentPresetName) &&
                !hasUnsavedChanges() && (
                  <div className="bg-muted rounded-full p-1">
                    <Heart
                      className="size-1"
                      stroke="var(--muted)"
                      fill="var(--muted-foreground)"
                    />
                  </div>
                )}
              <span className="truncate text-left font-medium capitalize">
                {hasUnsavedChanges() ? (
                  <>Custom (Unsaved)</>
                ) : (
                  presets[currentPresetName || "default"]?.label || "default"
                )}
              </span>
            </div>
            <ChevronDown className="size-4 shrink-0" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[400px] p-0" align="center">
          <Command className="h-100 w-full rounded-lg border shadow-md">
            <div className="flex w-full items-center">
              <div className="flex w-full items-center border-b px-3 py-1">
                <Search className="size-4 shrink-0 opacity-50" />
                <Input
                  placeholder="Search themes..."
                  className="border-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
            <div className="flex items-center justify-between px-4 py-2">
              <div className="text-muted-foreground text-xs">
                {filteredPresets.length} theme
                {filteredPresets.length !== 1 ? "s" : ""}
              </div>
              <ThemeControls />
            </div>
            
            <Separator />

            <ScrollArea className="h-[calc(100vh-20px)] overflow-y-auto pr-2">
              <CommandEmpty>No themes found.</CommandEmpty>
              {/* Saved Themes Group */}
              {filteredSavedThemes.length > 0 && (
                <>
                  <CommandGroup
                    heading={
                      <div className="flex w-full items-center justify-between">
                        <span>Saved Themes</span>
                        <div>
                          <Button
                            variant="link"
                            size="sm"
                            className="text-muted-foreground hover:text-foreground flex h-6 items-center gap-1.5 p-0 text-xs"
                          >
                            <Settings />
                            <span>Manage</span>
                          </Button>
                        </div>
                      </div>
                    }
                  >
                    {filteredSavedThemes
                      .filter((name) => name !== "default" && isSavedTheme(name))
                      .map((presetName, index) => (
                        <CommandItem
                          key={`${presetName}-${index}`}
                          value={`${presetName}-${index}`}
                          onSelect={() => {
                            applyThemePreset(presetName);
                            setSearch("");
                          }}
                          className="data-[highlighted]:bg-secondary/50 flex items-center gap-2 py-2"
                        >
                          <ThemeColors presetName={presetName} mode={mode} />
                          <div className="flex flex-1 items-center gap-2">
                            <span className="line-clamp-1 text-sm font-medium capitalize">
                              {presets[presetName]?.label || presetName}
                            </span>
                            {presets[presetName] && isThemeNew(presets[presetName]) && (
                              <Badge variant="secondary" className="rounded-full text-xs">
                                New
                              </Badge>
                            )}
                          </div>
                          {presetName === currentPresetName && (
                            <Check className="h-4 w-4 shrink-0 opacity-70" />
                          )}
                        </CommandItem>
                      ))}
                  </CommandGroup>
                  <Separator className="my-2" />
                </>
              )}

              {filteredSavedThemes.length === 0 && search.trim() === "" && (
                <>
                  <div className="text-muted-foreground flex items-center gap-1.5 px-2 pt-2 text-xs">
                    <div className="flex items-center gap-1 rounded-md border px-2 py-1">
                      <Heart className="size-3" />
                      <span>Save</span>
                    </div>
                    <span>a theme to find it here.</span>
                  </div>
                  <Separator className="my-2" />
                </>
              )}

              {/* Default Theme Group */}
              {filteredDefaultThemes.length > 0 && (
                <CommandGroup heading="Built-in Themes">
                  {filteredDefaultThemes.map((presetName, index) => (
                    <CommandItem
                      key={`${presetName}-${index}`}
                      value={`${presetName}-${index}`}
                      onSelect={() => {
                        applyThemePreset(presetName);
                        setSearch("");
                      }}
                      className="data-[highlighted]:bg-secondary/50 flex items-center gap-2 py-2"
                    >
                      <ThemeColors presetName={presetName} mode={mode} />
                      <div className="flex flex-1 items-center gap-2">
                        <span className="text-sm font-medium capitalize">
                          {presets[presetName]?.label || presetName}
                        </span>
                        {presets[presetName] && isThemeNew(presets[presetName]) && (
                          <Badge variant="secondary" className="rounded-full text-xs">
                            New
                          </Badge>
                        )}
                      </div>
                      {presetName === currentPresetName && (
                        <Check className="h-4 w-4 shrink-0 opacity-70" />
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </ScrollArea>
          </Command>
        </PopoverContent>
      </Popover>

      {withCycleThemes && (
        <div className="flex items-center shrink-0">
          <ThemePresetCycleControls
            filteredPresets={filteredPresets}
            currentPresetName={currentPresetName || "default"}
            className={className}
            disabled={props.disabled}
          />
        </div>
      )}
    </div>
  );
};

export default ThemePresetSelect;
