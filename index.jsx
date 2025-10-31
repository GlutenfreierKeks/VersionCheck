import React, { useState, useRef, useEffect } from 'react';
import { Download, Upload, Play, Trash2, Plus, GripVertical, ChevronDown, ChevronRight, X } from 'lucide-react';

const MinecraftCodeDesigner = () => {
  const [blocks, setBlocks] = useState([]);
  const [draggedBlock, setDraggedBlock] = useState(null);
  const [previewMode, setPreviewMode] = useState('sequence');
  const [expandedCategories, setExpandedCategories] = useState({
    movement: true,
    blocks: true,
    chat: true,
    logic: true,
    events: true,
    rotation: true,
    gui: true,
    combat: true,
    info: true
  });

  const blockCategories = {
    movement: {
      name: 'Player Movement',
      color: 'bg-blue-500',
      blocks: [
        { id: 'move', label: 'move', params: [{ type: 'number', default: 1, label: 'blocks' }], suffix: 'block(s)' },
        { id: 'jump', label: 'jump', params: [] },
        { id: 'sneak', label: 'sneak', params: [{ type: 'dropdown', options: ['start', 'stop'], default: 'start' }] },
        { id: 'sprint', label: 'sprint', params: [{ type: 'dropdown', options: ['start', 'stop'], default: 'start' }] },
        { id: 'setVelocity', label: 'set velocity', params: [
          { type: 'number', default: 0, label: 'X' },
          { type: 'number', default: 0, label: 'Y' },
          { type: 'number', default: 0, label: 'Z' }
        ] }
      ]
    },
    blocks: {
      name: 'Block Interaction',
      color: 'bg-green-500',
      blocks: [
        { id: 'place', label: 'place', params: [
          { type: 'dropdown', options: ['Oak Plank', 'Stone', 'Dirt', 'Cobblestone', 'Glass', 'Wool'], default: 'Oak Plank', label: 'block' },
          { type: 'text', default: '~', label: 'X' },
          { type: 'text', default: '~', label: 'Y' },
          { type: 'text', default: '~', label: 'Z' }
        ], suffix: 'at position' },
        { id: 'break', label: 'break block at', params: [
          { type: 'text', default: '~', label: 'X' },
          { type: 'text', default: '~', label: 'Y' },
          { type: 'text', default: '~', label: 'Z' }
        ] },
        { id: 'check', label: 'get block at', params: [
          { type: 'text', default: '~', label: 'X' },
          { type: 'text', default: '~', label: 'Y' },
          { type: 'text', default: '~', label: 'Z' }
        ] }
      ]
    },
    rotation: {
      name: 'Look & Rotation',
      color: 'bg-cyan-500',
      blocks: [
        { id: 'lookAt', label: 'look at position', params: [
          { type: 'text', default: '~', label: 'X' },
          { type: 'text', default: '~', label: 'Y' },
          { type: 'text', default: '~', label: 'Z' }
        ] },
        { id: 'lookAtEntity', label: 'look at entity', params: [
          { type: 'text', default: 'Zombie', label: 'entity name' }
        ] },
        { id: 'rotateHead', label: 'rotate head to', params: [
          { type: 'text', default: '~', label: 'yaw' },
          { type: 'text', default: '~', label: 'pitch' }
        ] }
      ]
    },
    gui: {
      name: 'GUI & Inventory',
      color: 'bg-indigo-500',
      blocks: [
        { id: 'guiClick', label: 'click GUI slot', params: [
          { type: 'number', default: 0, label: 'slot' },
          { type: 'dropdown', options: ['LEFT', 'RIGHT', 'SHIFT', 'DROP'], default: 'LEFT', label: 'click type' }
        ] },
        { id: 'guiClose', label: 'close GUI', params: [] },
        { id: 'swapHotbar', label: 'swap hotbar slots', params: [
          { type: 'number', default: 0, label: 'slot 1' },
          { type: 'number', default: 1, label: 'slot 2' }
        ] },
        { id: 'dropItem', label: 'drop item', params: [
          { type: 'dropdown', options: ['single', 'stack'], default: 'single', label: 'amount' }
        ] },
        { id: 'selectHotbar', label: 'select hotbar slot', params: [
          { type: 'number', default: 0, label: 'slot (0-8)' }
        ] }
      ]
    },
    combat: {
      name: 'Combat',
      color: 'bg-red-500',
      blocks: [
        { id: 'attack', label: 'attack target', params: [] },
        { id: 'useItem', label: 'use item', params: [] },
        { id: 'attackEntity', label: 'attack entity', params: [
          { type: 'text', default: 'nearest', label: 'target' }
        ] },
        { id: 'blockWithShield', label: 'block with shield', params: [
          { type: 'dropdown', options: ['start', 'stop'], default: 'start' }
        ] }
      ]
    },
    info: {
      name: 'Information',
      color: 'bg-teal-500',
      blocks: [
        { id: 'getPlayerPos', label: 'get player position', params: [] },
        { id: 'getPlayerHealth', label: 'get player health', params: [] },
        { id: 'getPlayerHunger', label: 'get player hunger', params: [] },
        { id: 'getNearbyEntities', label: 'get nearby entities', params: [
          { type: 'number', default: 10, label: 'radius' }
        ] },
        { id: 'checkInventory', label: 'check inventory for', params: [
          { type: 'text', default: 'diamond', label: 'item name' }
        ] }
      ]
    },
    chat: {
      name: 'Chat/Command',
      color: 'bg-purple-500',
      blocks: [
        { id: 'sendChat', label: 'send chat message', params: [{ type: 'text', default: 'Hello!', label: 'message' }] },
        { id: 'sendCommand', label: 'send command', params: [{ type: 'text', default: '/help', label: 'command' }] },
        { id: 'readChat', label: 'read last chat message', params: [] }
      ]
    },
    logic: {
      name: 'Logic',
      color: 'bg-yellow-500',
      blocks: [
        { id: 'if', label: 'if', params: [{ type: 'condition', default: 'true' }], container: true },
        { id: 'wait', label: 'wait', params: [{ type: 'number', default: 1, label: 'seconds' }], suffix: 'second(s)' },
        { id: 'repeat', label: 'repeat', params: [{ type: 'number', default: 10, label: 'times' }], container: true },
        { id: 'while', label: 'while', params: [{ type: 'condition', default: 'true' }], container: true }
      ]
    },
    events: {
      name: 'Events',
      color: 'bg-orange-500',
      blocks: [
        { id: 'onTick', label: 'on tick', params: [], event: true },
        { id: 'onKeyPress', label: 'on key press', params: [{ type: 'dropdown', options: ['W', 'A', 'S', 'D', 'SPACE', 'SHIFT', 'Q', 'E'], default: 'W' }], event: true },
        { id: 'onBlockBreak', label: 'on block break', params: [], event: true },
        { id: 'onPlayerHit', label: 'on player hit', params: [], event: true },
        { id: 'onChatMessage', label: 'on chat message', params: [{ type: 'text', default: '', label: 'contains' }], event: true }
      ]
    }
  };

  const addBlock = (category, blockType) => {
    const newBlock = {
      uid: Date.now() + Math.random(),
      category,
      type: blockType.id,
      label: blockType.label,
      params: blockType.params?.map(p => ({ ...p, value: p.default })) || [],
      suffix: blockType.suffix || '',
      container: blockType.container || false,
      event: blockType.event || false,
      children: blockType.container ? [] : null
    };
    setBlocks([...blocks, newBlock]);
  };

  const updateBlockParam = (uid, paramIndex, value) => {
    setBlocks(blocks.map(block => 
      block.uid === uid 
        ? { ...block, params: block.params.map((p, i) => i === paramIndex ? { ...p, value } : p) }
        : block
    ));
  };

  const removeBlock = (uid) => {
    setBlocks(blocks.filter(block => block.uid !== uid));
  };

  const exportModule = () => {
    const exportData = {
      version: '1.0.0',
      minecraft_version: '1.21.5',
      mod_target: 'mioclient/oyvey-ported',
      timestamp: new Date().toISOString(),
      blocks: blocks.map(block => ({
        type: block.type,
        category: block.category,
        parameters: block.params.map(p => ({ type: p.type, value: p.value }))
      }))
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `minecraft-script-${Date.now()}.mcd.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importModule = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        const importedBlocks = data.blocks.map((block, index) => {
          const categoryBlocks = blockCategories[block.category]?.blocks || [];
          const blockDef = categoryBlocks.find(b => b.id === block.type);
          
          return {
            uid: Date.now() + index + Math.random(),
            category: block.category,
            type: block.type,
            label: blockDef?.label || block.type,
            params: block.parameters.map((p, i) => ({
              ...blockDef?.params?.[i],
              value: p.value
            })),
            suffix: blockDef?.suffix || '',
            container: blockDef?.container || false,
            event: blockDef?.event || false,
            children: blockDef?.container ? [] : null
          };
        });
        setBlocks(importedBlocks);
      } catch (err) {
        alert('Invalid file format');
      }
    };
    reader.readAsText(file);
  };

  const toggleCategory = (cat) => {
    setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const getCategoryColor = (category) => {
    return blockCategories[category]?.color || 'bg-gray-500';
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-md px-6 py-4 flex items-center justify-between border-b-4 border-green-500">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-xl">
            M
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Minecraft Code Designer</h1>
            <p className="text-xs text-gray-500">Visual Programming for Minecraft 1.21.5 (mioclient/oyvey-ported)</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <label className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg cursor-pointer flex items-center space-x-2 transition-all shadow-md hover:shadow-lg">
            <Upload size={18} />
            <span className="font-medium">Import Module</span>
            <input type="file" accept=".json,.mcd.json" onChange={importModule} className="hidden" />
          </label>
          
          <button 
            onClick={exportModule}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-all shadow-md hover:shadow-lg font-medium"
          >
            <Download size={18} />
            <span>Export Module</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Block Palette */}
        <aside className="w-72 bg-white shadow-lg overflow-y-auto border-r-2 border-gray-200">
          <div className="p-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white">
            <h2 className="text-lg font-bold">Block Palette</h2>
            <p className="text-xs opacity-90 mt-1">Click blocks to add to workspace</p>
          </div>
          
          <div className="p-3 space-y-2">
            {Object.entries(blockCategories).map(([key, category]) => (
              <div key={key} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleCategory(key)}
                  className={`w-full ${category.color} text-white px-3 py-2 flex items-center justify-between font-medium hover:opacity-90 transition-all`}
                >
                  <span>{category.name}</span>
                  {expandedCategories[key] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </button>
                
                {expandedCategories[key] && (
                  <div className="p-2 space-y-2 bg-gray-50">
                    {category.blocks.map((block) => (
                      <button
                        key={block.id}
                        onClick={() => addBlock(key, block)}
                        className={`w-full ${category.color} text-white px-3 py-2 rounded-md hover:opacity-90 transition-all text-sm font-medium shadow-sm hover:shadow-md flex items-center space-x-2`}
                      >
                        <Plus size={14} />
                        <span>{block.label}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </aside>

        {/* Workspace */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="bg-white border-b-2 border-gray-200 px-6 py-3 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">Workspace ({blocks.length} blocks)</h2>
            <button
              onClick={() => setBlocks([])}
              className="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-lg flex items-center space-x-2 text-sm transition-all shadow-sm hover:shadow-md"
            >
              <Trash2 size={16} />
              <span>Clear All</span>
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-gray-50 to-blue-50">
            <div className="max-w-4xl mx-auto space-y-3">
              {blocks.length === 0 ? (
                <div className="text-center py-20 text-gray-400">
                  <p className="text-lg font-medium">Click blocks from the palette to get started</p>
                  <p className="text-sm mt-2">Create custom Minecraft functions visually</p>
                  <p className="text-xs mt-4 text-gray-500">Supports: Movement, Blocks, Look/Rotation, GUI, Combat, Info & more</p>
                </div>
              ) : (
                blocks.map((block) => (
                  <div
                    key={block.uid}
                    className={`${getCategoryColor(block.category)} text-white rounded-lg shadow-md hover:shadow-lg transition-all p-4 flex items-start space-x-3`}
                  >
                    <GripVertical className="mt-1 opacity-50" size={20} />
                    
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold">{block.label}</span>
                        
                        {block.params.map((param, idx) => (
                          <React.Fragment key={idx}>
                            {param.label && <span className="text-xs opacity-75">{param.label}:</span>}
                            {param.type === 'dropdown' ? (
                              <select
                                value={param.value}
                                onChange={(e) => updateBlockParam(block.uid, idx, e.target.value)}
                                className="bg-white bg-opacity-30 border border-white border-opacity-50 rounded px-2 py-1 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-white"
                              >
                                {param.options.map(opt => (
                                  <option key={opt} value={opt} className="text-gray-800">{opt}</option>
                                ))}
                              </select>
                            ) : (
                              <input
                                type={param.type === 'number' ? 'number' : 'text'}
                                value={param.value}
                                onChange={(e) => updateBlockParam(block.uid, idx, e.target.value)}
                                className="bg-white bg-opacity-30 border border-white border-opacity-50 rounded px-2 py-1 text-sm w-20 font-medium focus:outline-none focus:ring-2 focus:ring-white"
                              />
                            )}
                          </React.Fragment>
                        ))}
                        
                        {block.suffix && <span className="opacity-90">{block.suffix}</span>}
                      </div>
                      
                      {block.event && (
                        <div className="mt-2 text-xs bg-white bg-opacity-20 rounded px-2 py-1 inline-block">
                          🎯 Event Trigger
                        </div>
                      )}
                      {block.container && (
                        <div className="mt-2 text-xs bg-white bg-opacity-20 rounded px-2 py-1 inline-block">
                          📦 Container Block
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={() => removeBlock(block.uid)}
                      className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded p-1.5 transition-all"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </main>

        {/* Preview Panel */}
        <aside className="w-80 bg-white shadow-lg border-l-2 border-gray-200 overflow-y-auto">
          <div className="p-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
            <h2 className="text-lg font-bold">Script Preview</h2>
            <p className="text-xs opacity-90 mt-1">Execution sequence visualization</p>
          </div>
          
          <div className="p-4">
            {blocks.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-8">No blocks added yet</p>
            ) : (
              <div className="space-y-2">
                <div className="text-xs font-bold text-gray-600 mb-3">Execution Order:</div>
                {blocks.map((block, idx) => (
                  <div key={block.uid} className="flex items-start space-x-2 text-sm">
                    <span className="bg-gray-200 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <span className="font-medium text-gray-700">{block.label}</span>
                      {block.params.length > 0 && (
                        <div className="text-xs text-gray-500 mt-0.5">
                          {block.params.map((p, i) => (
                            <span key={i}>{p.value}{i < block.params.length - 1 ? ', ' : ''}</span>
                          ))}
                        </div>
                      )}
                      <div className="text-xs text-gray-400 mt-0.5">
                        {block.category}
                      </div>
                    </div>
                  </div>
                ))}
                
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="text-xs font-bold text-gray-600 mb-2">Statistics:</div>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>Total Blocks:</span>
                      <span className="font-bold">{blocks.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Event Triggers:</span>
                      <span className="font-bold">{blocks.filter(b => b.event).length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Logic Blocks:</span>
                      <span className="font-bold">{blocks.filter(b => b.container).length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Categories Used:</span>
                      <span className="font-bold">{new Set(blocks.map(b => b.category)).size}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};

export default MinecraftCodeDesigner;