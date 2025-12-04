import { ArrowRight, CheckCircle2, Globe, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import PageTransition from "@/components/PageTransition";

const AboutPage = () => {
  return (
    <PageTransition>
      <div className="space-y-16 pb-16">
        {/* Hero Section */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/10 via-primary/5 to-background border border-primary/10 p-12 md:p-24 text-center">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1519681393798-3828fb4090bb?auto=format&fit=crop&q=80')] opacity-[0.03] bg-cover bg-center mix-blend-overlay pointer-events-none"></div>
          <div className="relative z-10 max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm font-medium text-primary backdrop-blur-sm">
              <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse"></span>
              Revolutionizing Government Contracting
            </div>
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-foreground">
              Empowering <span className="text-primary">GEDS IO</span> with Intelligent Insights
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              We bridge the gap between complex government opportunities and actionable intelligence, enabling your team to win more contracts with less effort.
            </p>
            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <Button size="lg" className="h-12 px-8 text-lg shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all">
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button variant="outline" size="lg" className="h-12 px-8 text-lg backdrop-blur-sm bg-background/50">
                Learn More
              </Button>
            </div>
          </div>
        </section>

        {/* Mission Section */}
        <section className="grid md:grid-cols-2 gap-12 items-center max-w-6xl mx-auto px-4">
          <div className="space-y-6">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Our Mission</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              At FedOps, our mission is to democratize access to government contracting opportunities through advanced AI and data analytics. We believe that every organization, regardless of size, deserves the tools to compete effectively in the federal marketplace.
            </p>
            <div className="space-y-4 pt-4">
              {[
                "Simplify complex solicitation documents",
                "Accelerate proposal development",
                "Enhance compliance and risk management",
                "Provide real-time market intelligence"
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0" />
                  <span className="text-lg">{item}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-transparent rounded-2xl transform rotate-3 scale-105 blur-lg opacity-50"></div>
            <Card className="relative overflow-hidden border-none shadow-2xl bg-card/50 backdrop-blur-sm">
              <CardContent className="p-0">
                <img 
                  src="https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&q=80" 
                  alt="Team collaboration" 
                  className="w-full h-full object-cover aspect-video hover:scale-105 transition-transform duration-700"
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Features Grid */}
        <section className="max-w-7xl mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Why Choose FedOps?</h2>
            <p className="text-lg text-muted-foreground">
              Our platform combines cutting-edge technology with deep industry expertise to deliver a superior contracting experience.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: "AI-Powered Analysis",
                description: "Instantly analyze thousands of pages of documentation to extract key requirements and risks."
              },
              {
                icon: Shield,
                title: "Compliance First",
                description: "Built-in compliance checks ensure your proposals meet all federal regulations and standards."
              },
              {
                icon: Globe,
                title: "Market Intelligence",
                description: "Gain a competitive edge with real-time insights into agency spending and competitor activity."
              }
            ].map((feature, index) => (
              <Card key={index} className="group hover:shadow-xl transition-all duration-300 border-primary/10 bg-gradient-to-b from-card to-card/50">
                <CardContent className="p-8 space-y-4">
                  <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <feature.icon className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative overflow-hidden rounded-3xl bg-primary text-primary-foreground p-12 md:p-20 text-center mx-4 md:mx-0">
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80')] opacity-10 bg-cover bg-center mix-blend-overlay"></div>
          <div className="relative z-10 max-w-3xl mx-auto space-y-8">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight">Ready to Transform Your Workflow?</h2>
            <p className="text-xl text-primary-foreground/80 max-w-2xl mx-auto">
              Join the growing number of government contractors who trust FedOps to power their growth.
            </p>
            <Button size="lg" variant="secondary" className="h-14 px-10 text-lg font-semibold shadow-xl hover:shadow-2xl hover:scale-105 transition-all">
              Start Your Free Trial
            </Button>
          </div>
        </section>
      </div>
    </PageTransition>
  );
};

export default AboutPage;
