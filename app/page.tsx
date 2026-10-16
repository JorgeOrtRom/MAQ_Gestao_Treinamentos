'use client';

import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Users, Award, BookOpen, CheckCircle, AlertTriangle, FileText, Upload, Save, Plus, Search, Printer, Layers, ExternalLink, Trash2, Filter
} from 'lucide-react';

const SUPABASE_URL = 'https://qpmgzztaduetfrjcvswo.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_tGyuT8NnOb67vrbcC8dTFA_wYrn2hkP';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export default function EnterpriseDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [colaboradores, setColaboradores] = useState<any[]>([]);
  const [treinamentos, setTreinamentos] = useState<any[]>([]);
  const [registros, setRegistros] = useState<any[]>([]);
  const [matrizLnt, setMatrizLnt] = useState<any[]>([]);
  const [selectedColab, setSelectedColab] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Formulários de cadastro
  const [novoColab, setNovoColab] = useState({ nome: '', cargo: '', departamento: '', gestor: '' });
  const [novoTreino, setNovoTreino] = useState({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
  const [novaMatriz, setNovaMatriz] = useState({ cargo: '', treinamento_id: '' });

  useEffect(() => {
    fetchInitialData();
  }, []);

  async function fetchInitialData() {
    setLoading(true);
    const { data: colabs } = await supabase.from('colaboradores').select('*').order('nome');
    const { data: treinos } = await supabase.from('treinamentos').select('*').order('nome_curso');
    const { data: regs } = await supabase.from('registros').select('*, colaboradores(nome, departamento, cargo), treinamentos(nome_curso, carga_horaria, classificacao)');
    const { data: matriz } = await supabase.from('matriz_cargo_treinamento').select('*, treinamentos(nome_curso, carga_horaria)');

    if (colabs) setColaboradores(colabs);
    if (treinos) setTreinamentos(treinos);
    if (regs) setRegistros(regs);
    if (matriz) setMatrizLnt(matriz);
    if (colabs && colabs.length > 0 && !selectedColab) setSelectedColab(colabs[0].id);
    setLoading(false);
  }

  // Métricas do Dashboard
  const totalHoras = registros.reduce((acc, r) => acc + (Number(r.treinamentos?.carga_horaria) || 0), 0);
  const totalConcluidos = registros.filter(r => r.status === 'Concluído' || r.status === '🟢 Concluído').length;
  const statusData = [
    { name: '🟢 Concluídos', value: totalConcluidos },
    { name: '🔴 Pendentes LNT', value: Math.max(0, matrizLnt.length - totalConcluidos) }
  ];
  const COLORS = ['#10B981', '#EF4444'];

  // Ações no Supabase
  async function handleAddColaborador(e: React.FormEvent) {
    e.preventDefault();
    if (!novoColab.nome || !novoColab.cargo) return alert('Preencha os campos obrigatórios!');
    const { error } = await supabase.from('colaboradores').insert([novoColab]);
    if (!error) {
      setNovoColab({ nome: '', cargo: '', departamento: '', gestor: '' });
      fetchInitialData();
      alert('Colaborador cadastrado com sucesso!');
    } else {
      alert('Erro ao cadastrar: ' + error.message);
    }
  }

  async function handleAddTreinamento(e: React.FormEvent) {
    e.preventDefault();
    if (!novoTreino.nome_curso) return alert('Informe o nome do treinamento!');
    const { error } = await supabase.from('treinamentos').insert([novoTreino]);
    if (!error) {
      setNovoTreino({ nome_curso: '', carga_horaria: 1, frequencia: 'ANUAL', classificacao: 'Exigência da função', aplicador_padrao: '' });
      fetchInitialData();
      alert('Treinamento cadastrado com sucesso!');
    } else {
      alert('Erro ao cadastrar: ' + error.message);
    }
  }

  async function handleAddMatriz(e: React.FormEvent) {
    e.preventDefault();
    if (!novaMatriz.cargo || !novaMatriz.treinamento_id) return alert('Selecione o cargo e o treinamento!');
    const { error } = await supabase.from('matriz_cargo_treinamento').insert([novaMatriz]);
    if (!error) {
      setNovaMatriz({ cargo: '', treinamento_id: '' });
      fetchInitialData();
      alert('Vínculo criado na Matriz LNT!');
    } else {
      alert('Erro na Matriz LNT: ' + error.message);
    }
  }

  async function handleDeleteMatrizItem(id: string) {
    if (!confirm('Deseja remover este requisito da Matriz LNT?')) return;
    await supabase.from('matriz_cargo_treinamento').delete().eq('id', id);
    fetchInitialData();
  }

  async function handleSalvarRegistro(treinamentoId: string, status: string, dataAplicacao: string, aplicador: string, cargoAplicador: string, arquivoFile: File | null) {
    let urlForms = '';

    if (arquivoFile) {
      const fileName = `evidencia_${selectedColab}_${treinamentoId}_${Date.now()}.pdf`;
      const { data, error } = await supabase.storage.from('evidencias').upload(fileName, arquivoFile);
      if (!error && data) {
        urlForms = supabase.storage.from('evidencias').getPublicUrl(data.path).data.publicUrl;
      }
    }

    if (status === '🟢 Concluído' || status === 'Concluído') {
      await supabase.from('registros').upsert({
        colaborador_id: selectedColab,
        treinamento_id: treinamentoId,
        data_realizacao: dataAplicacao,
        instrutor_nome: aplicador,
        aplicador_cargo: cargoAplicador,
        status: 'Concluído',
        url_forms: urlForms || undefined
      });
    } else {
      await supabase.from('registros').delete()
        .eq('colaborador_id', selectedColab)
        .eq('treinamento_id', treinamentoId);
    }

    await fetchInitialData();
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white font-sans">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg font-medium">Carregando MAQ Gestão de Treinamentos...</p>
        </div>
      </div>
    );
  }

  const filteredColaboradores = colaboradores.filter(c => 
    c.nome.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.departamento?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.cargo?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentColabData = colaboradores.find(c => c.id === selectedColab);
  const colabRegistros = registros.filter(r => r.colaborador_id === selectedColab);
  
  // Requisitos obrigatórios do cargo do colaborador selecionado
  const requisitosCargo = matrizLnt.filter(m => m.cargo === currentColabData?.cargo);
  const cargosExistentes = Array.from(new Set(colaboradores.map(c => c.cargo).filter(Boolean)));

  return (
    <div className="flex h-screen bg-slate-100 font-sans text-slate-800">
      {/* Menu Lateral */}
      <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col justify-between shadow-xl">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <Award className="w-8 h-8 text-blue-500" />
            <h1 className="text-xl font-bold tracking-wider">MAQ GESTÃO</h1>
          </div>

          <nav className="space-y-2">
            <button 
              onClick={() => setActiveTab('dashboard')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <BarChart className="w-5 h-5" /> Dashboard Executivo
            </button>
            <button 
              onClick={() => setActiveTab('colaborador')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'colaborador' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Users className="w-5 h-5" /> Lançamentos por Colaborador
            </button>
            <button 
              onClick={() => setActiveTab('matriz_lnt')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'matriz_lnt' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Layers className="w-5 h-5" /> Matriz LNT por Cargo
            </button>
            <button 
              onClick={() => setActiveTab('cadastro_colab')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'cadastro_colab' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <Plus className="w-5 h-5" /> Cadastrar Colaborador
            </button>
            <button 
              onClick={() => setActiveTab('catalogo')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition ${activeTab === 'catalogo' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
            >
              <BookOpen className="w-5 h-5" /> Catálogo Treinamentos
            </button>
          </nav>
        </div>

        <button onClick={() => window.print()} className="flex items-center gap-2 text-slate-400 hover:text-white transition">
          <Printer className="w-5 h-5" /> Imprimir Relatório
        </button>
      </aside>

      {/* Conteúdo Central */}
      <main className="flex-1 overflow-y-auto p-8">
        
        {/* 1. DASHBOARD EXECUTIVO */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Dashboard Executivo de Treinamentos</h2>
                <p className="text-slate-500 text-sm">Visão consolidada via Supabase PostgreSQL</p>
              </div>
            </header>

            <div className="grid grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Total Colaboradores</p>
                <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{colaboradores.length}</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Horas de Treinamento</p>
                <h3 className="text-3xl font-extrabold text-blue-600 mt-2">{totalHoras}h</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Conclusões Registradas</p>
                <h3 className="text-3xl font-extrabold text-emerald-600 mt-2">{totalConcluidos}</h3>
              </div>
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <p className="text-slate-500 text-sm font-medium">Requisitos na Matriz LNT</p>
                <h3 className="text-3xl font-extrabold text-amber-500 mt-2">{matrizLnt.length}</h3>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h4 className="text-lg font-bold text-slate-800 mb-4">Compliance da Matriz LNT</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={statusData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} dataKey="value">
                        {statusData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h4 className="text-lg font-bold text-slate-800 mb-4">Carga Horária por Treinamento</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={treinamentos}>
                      <XAxis dataKey="nome_curso" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="carga_horaria" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 2. LANÇAMENTO POR COLABORADOR */}
        {activeTab === 'colaborador' && (
          <div className="space-y-6">
            <header className="flex justify-between items-center border-b pb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Lançamentos e Histórico Individual</h2>
                <p className="text-slate-500 text-sm">Gerencie conclusões, datas e faça o upload de listas de presença em PDF</p>
              </div>

              <div className="flex gap-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                  <input 
                    type="text" 
                    placeholder="Filtrar colaborador..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9 pr-4 py-2 border rounded-lg text-sm bg-white shadow-sm outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <select 
                  value={selectedColab} 
                  onChange={(e) => setSelectedColab(e.target.value)}
                  className="px-4 py-2 bg-white border border-slate-300 rounded-lg shadow-sm font-semibold text-slate-700 outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {filteredColaboradores.map(c => (
                    <option key={c.id} value={c.id}>{c.nome} ({c.cargo})</option>
                  ))}
                </select>
              </div>
            </header>

            {currentColabData && (
              <div className="bg-slate-900 text-white p-6 rounded-xl shadow-lg flex justify-between items-center">
                <div>
                  <h3 className="text-2xl font-bold">{currentColabData.nome}</h3>
                  <p className="text-slate-300 text-sm mt-1">Cargo: <span className="font-semibold text-blue-400">{currentColabData.cargo}</span> | Setor: {currentColabData.departamento}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">GESTOR DIRETO</p>
                  <p className="font-semibold">{currentColabData.gestor || 'Não informado'}</p>
                </div>
              </div>
            )}

            {/* Aviso de Requisitos Obrigatórios do Cargo (LNT) */}
            {requisitosCargo.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-amber-800 text-sm flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div>
                  <strong>Requisitos Obrigatórios para o cargo ({currentColabData?.cargo}):</strong>
                  <span className="ml-2">{requisitosCargo.map(r => r.treinamentos?.nome_curso).join(', ')}</span>
                </div>
              </div>
            )}

            <div className="space-y-4 mt-6">
              {treinamentos.map(treino => {
                const reg = colabRegistros.find(r => r.treinamento_id === treino.id);
                const isConcluido = reg?.status === 'Concluído' || reg?.status === '🟢 Concluído';
                const isObrigatorioCargo = requisitosCargo.some(r => r.treinamento_id === treino.id);

                return (
                  <div key={treino.id} className={`bg-white p-6 rounded-xl border ${isObrigatorioCargo ? 'border-l-4 border-l-blue-500 border-slate-200' : 'border-slate-200'} shadow-sm flex items-center justify-between gap-6`}>
                    <div className="w-1/3">
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-slate-900 text-lg">{treino.nome_curso}</h4>
                        {isObrigatorioCargo && (
                          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded font-semibold">LNT Obrigatória</span>
                        )}
                      </div>
                      <p className="text-slate-500 text-sm">{treino.carga_horaria}h — {treino.classificacao}</p>
                      {reg?.url_forms && (
                        <a href={reg.url_forms} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2 font-medium">
                          <ExternalLink className="w-3 h-3" /> Ver Evidência Anexada
                        </a>
                      )}
                    </div>

                    <form 
                      onSubmit={(e: any) => {
                        e.preventDefault();
                        const status = e.target.status.value;
                        const data = e.target.data.value;
                        const aplicador = e.target.aplicador.value;
                        const cargo = e.target.cargo.value;
                        const file = e.target.arquivo.files[0] || null;
                        handleSalvarRegistro(treino.id, status, data, aplicador, cargo, file);
                      }}
                      className="flex-1 flex items-center gap-3"
                    >
                      <select name="status" defaultValue={isConcluido ? '🟢 Concluído' : '🔴 Pendente'} className="px-3 py-2 border rounded-lg text-sm bg-slate-50">
                        <option value="🔴 Pendente">🔴 Pendente</option>
                        <option value="🟢 Concluído">🟢 Concluído</option>
                      </select>

                      <input type="date" name="data" defaultValue={reg?.data_realizacao || new Date().toISOString().split('T')[0]} className="px-3 py-2 border rounded-lg text-sm bg-slate-50" />
                      <input type="text" name="aplicador" defaultValue={reg?.instrutor_nome || treino.aplicador_padrao || ''} placeholder="Instrutor/Aplicador" className="px-3 py-2 border rounded-lg text-sm w-36 bg-slate-50" />
                      <input type="text" name="cargo" defaultValue={reg?.aplicador_cargo || treino.aplicador_cargo_padrao || ''} placeholder="Cargo Aplicador" className="px-3 py-2 border rounded-lg text-sm w-32 bg-slate-50" />
                      <input type="file" name="arquivo" className="text-xs w-36" />

                      <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition">
                        <Save className="w-4 h-4" /> Salvar
                      </button>
                    </form>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. MATRIZ LNT POR CARGO */}
        {activeTab === 'matriz_lnt' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Matriz LNT (Levantamento de Necessidades de Treinamento)</h2>
              <p className="text-slate-500 text-sm">Associe treinamentos e normas obrigatórias aos cargos existentes</p>
            </header>

            <form onSubmit={handleAddMatriz} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex gap-4 items-end max-w-3xl">
              <div className="flex-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Cargo</label>
                <select 
                  value={novaMatriz.cargo} 
                  onChange={e => setNovaMatriz({...novaMatriz, cargo: e.target.value})}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  required
                >
                  <option value="">Selecione o cargo...</option>
                  {cargosExistentes.map(cargo => (
                    <option key={cargo} value={cargo}>{cargo}</option>
                  ))}
                </select>
              </div>

              <div className="flex-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Treinamento Requerido</label>
                <select 
                  value={novaMatriz.treinamento_id} 
                  onChange={e => setNovaMatriz({...novaMatriz, treinamento_id: e.target.value})}
                  className="w-full p-2 border rounded-lg text-sm bg-slate-50"
                  required
                >
                  <option value="">Selecione o curso...</option>
                  {treinamentos.map(t => (
                    <option key={t.id} value={t.id}>{t.nome_curso}</option>
                  ))}
                </select>
              </div>

              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
                <Plus className="w-4 h-4" /> Vincular LNT
              </button>
            </form>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs uppercase font-semibold">
                  <tr>
                    <th className="p-4">Cargo / Função</th>
                    <th className="p-4">Treinamento Requerido</th>
                    <th className="p-4 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {matrizLnt.map(m => (
                    <tr key={m.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-900">{m.cargo}</td>
                      <td className="p-4 text-blue-600 font-medium">{m.treinamentos?.nome_curso}</td>
                      <td className="p-4 text-right">
                        <button onClick={() => handleDeleteMatrizItem(m.id)} className="text-red-500 hover:text-red-700 transition p-1">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 4. CADASTRO DE COLABORADORES */}
        {activeTab === 'cadastro_colab' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Novo Colaborador</h2>
              <p className="text-slate-500 text-sm">Adicionar funcionários à base corporativa do Supabase</p>
            </header>

            <form onSubmit={handleAddColaborador} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-2xl space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nome Completo</label>
                <input type="text" value={novoColab.nome} onChange={e => setNovoColab({...novoColab, nome: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Cargo</label>
                  <input type="text" value={novoColab.cargo} onChange={e => setNovoColab({...novoColab, cargo: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Departamento / Setor</label>
                  <input type="text" value={novoColab.departamento} onChange={e => setNovoColab({...novoColab, departamento: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Gestor Direto</label>
                <input type="text" value={novoColab.gestor} onChange={e => setNovoColab({...novoColab, gestor: e.target.value})} className="w-full p-2 border rounded-lg bg-slate-50" />
              </div>

              <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-semibold flex items-center gap-2">
                <Plus className="w-5 h-5" /> Cadastrar Colaborador
              </button>
            </form>
          </div>
        )}

        {/* 5. CATÁLOGO DE TREINAMENTOS */}
        {activeTab === 'catalogo' && (
          <div className="space-y-6">
            <header className="border-b pb-4">
              <h2 className="text-2xl font-bold text-slate-900">Catálogo Geral de Treinamentos</h2>
              <p className="text-slate-500 text-sm">Cursos, procedimentos operacionais (PO/IT) e normas regulamentadoras</p>
            </header>

            <form onSubmit={handleAddTreinamento} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm grid grid-cols-5 gap-4 items-end">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Nome / Norma</label>
                <input type="text" value={novoTreino.nome_curso} onChange={e => setNovoTreino({...novoTreino, nome_curso: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Carga Horária (h)</label>
                <input type="number" step="0.5" value={novoTreino.carga_horaria} onChange={e => setNovoTreino({...novoTreino, carga_horaria: parseFloat(e.target.value)})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Frequência</label>
                <input type="text" value={novoTreino.frequencia} onChange={e => setNovoTreino({...novoTreino, frequencia: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Classificação</label>
                <input type="text" value={novoTreino.classificacao} onChange={e => setNovoTreino({...novoTreino, classificacao: e.target.value})} className="w-full p-2 border rounded-lg text-sm bg-slate-50" />
              </div>
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2">
                <Plus className="w-4 h-4" /> Criar Curso
              </button>
            </form>

            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs uppercase font-semibold">
                  <tr>
                    <th className="p-4">Treinamento / Norma</th>
                    <th className="p-4">Carga Horária</th>
                    <th className="p-4">Frequência</th>
                    <th className="p-4">Classificação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {treinamentos.map(t => (
                    <tr key={t.id} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-900">{t.nome_curso}</td>
                      <td className="p-4">{t.carga_horaria} horas</td>
                      <td className="p-4">{t.frequencia}</td>
                      <td className="p-4">{t.classificacao}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}